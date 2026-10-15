"""Etapa H — scripts de backup e restauração (scripts/backup_dump.sh, backup_restore_check.sh).

Sem PostgreSQL só rodam as conferências de sintaxe e de configuração (saída 2). Com
``TEST_DATABASE_URL`` (e pg_dump/pg_restore/psql/age no PATH) o ciclo inteiro roda: dump
criptografado → restore em banco temporário → contagens iguais. O servidor de restauração é o
mesmo do teste (precisa de CREATE DATABASE); use ``RESTORE_CHECK_ADMIN_URL`` se o papel de
teste não tiver essa permissão.
"""

from __future__ import annotations

import os
import shutil
import subprocess
from pathlib import Path

import pytest
from sqlalchemy.engine import make_url

from tests.conftest import get_test_database_url, requires_postgres

ROOT = Path(__file__).resolve().parent.parent
SCRIPTS = ROOT / "scripts"
DUMP = SCRIPTS / "backup_dump.sh"
CHECK = SCRIPTS / "backup_restore_check.sh"

pytestmark = pytest.mark.skipif(shutil.which("bash") is None, reason="precisa de bash")

FERRAMENTAS = ("pg_dump", "pg_restore", "psql", "age", "age-keygen", "sha256sum")
tem_ferramentas = all(shutil.which(t) for t in FERRAMENTAS)
requires_tools = pytest.mark.skipif(not tem_ferramentas, reason="precisa de pg_dump, pg_restore, psql e age")


def run(script: Path, *args: str, env: dict | None = None) -> subprocess.CompletedProcess:
    base = {k: v for k, v in os.environ.items() if not k.startswith(("BACKUP_", "SOURCE_", "RESTORE_", "AGE_", "DATABASE_URL"))}
    base.update(env or {})
    return subprocess.run(["bash", str(script), *args], capture_output=True, text=True, env=base, timeout=300)


def libpq(url: str, database: str | None = None) -> str:
    parsed = make_url(url).set(drivername="postgresql")
    if database:
        parsed = parsed.set(database=database)
    return parsed.render_as_string(hide_password=False)


@pytest.mark.parametrize("script", [DUMP, CHECK], ids=lambda p: p.name)
def test_sintaxe_bash(script):
    result = subprocess.run(["bash", "-n", str(script)], capture_output=True, text=True)
    assert result.returncode == 0, result.stderr


def test_scripts_sao_executaveis():
    for script in (DUMP, CHECK):
        assert os.access(script, os.X_OK), f"{script.name} precisa de chmod +x"


def test_scripts_nao_imprimem_nem_ligam_xtrace():
    for script in (DUMP, CHECK):
        text = script.read_text(encoding="utf-8")
        assert "set +x" in text and "set -x" not in text.replace("set +x", "")
        assert "echo \"$DATABASE_URL" not in text and "echo \"$PGURL" not in text


@requires_tools
def test_backup_dump_sem_configuracao_sai_com_2():
    assert run(DUMP).returncode == 2
    sem_chave = run(DUMP, env={"DATABASE_URL": "postgresql://x@127.0.0.1:1/x"})
    assert sem_chave.returncode == 2 and "BACKUP_AGE_RECIPIENT" in sem_chave.stderr
    chave_privada = run(
        DUMP,
        env={"DATABASE_URL": "postgresql://x@127.0.0.1:1/x", "BACKUP_AGE_RECIPIENT": "AGE-SECRET-KEY-1ABC", "BACKUP_DRY_RUN": "1"},
    )
    assert chave_privada.returncode == 2 and "PÚBLICA" in chave_privada.stderr


@requires_tools
def test_backup_dump_exige_destino_https():
    result = run(
        DUMP,
        env={
            "DATABASE_URL": "postgresql://x@127.0.0.1:1/x",
            "BACKUP_AGE_RECIPIENT": "age1abc",
            "BACKUP_S3_ENDPOINT": "http://minio:9000",
            "BACKUP_S3_BUCKET": "b",
            "BACKUP_S3_ACCESS_KEY_ID": "i",
            "BACKUP_S3_SECRET_ACCESS_KEY": "s",
        },
    )
    assert result.returncode == 2 and "https" in result.stderr


@requires_tools
def test_restore_check_sem_fonte_nem_arquivo_sai_com_2():
    result = run(CHECK)
    assert result.returncode == 2


@requires_tools
def test_restore_check_arquivo_inexistente(tmp_path):
    result = run(CHECK, "--dump", str(tmp_path / "nao-existe.dump"), "--sem-fonte")
    assert result.returncode == 2


@requires_postgres
@requires_tools
class TestCicloComPostgres:
    @pytest.fixture()
    def urls(self, tmp_path):
        source = libpq(get_test_database_url())
        admin = os.environ.get("RESTORE_CHECK_ADMIN_URL") or libpq(get_test_database_url(), "postgres")
        probe = subprocess.run(["psql", libpq(admin), "-Atc", "SELECT rolcreatedb OR rolsuper FROM pg_roles WHERE rolname=current_user"],
                               capture_output=True, text=True)
        if probe.returncode != 0 or probe.stdout.strip() != "t":
            pytest.skip("o papel do servidor de teste não pode CREATE DATABASE (defina RESTORE_CHECK_ADMIN_URL)")
        return source, libpq(admin)

    def test_restore_check_com_dump_novo_confere_contagens(self, app, urls):
        source, admin = urls
        result = run(CHECK, env={"SOURCE_DATABASE_URL": source, "RESTORE_ADMIN_URL": admin})
        assert result.returncode == 0, result.stdout + result.stderr
        assert "RESULTADO: OK" in result.stdout
        assert "plans|" in result.stdout
        assert make_url(source).password is None or make_url(source).password not in (result.stdout + result.stderr)
        # O banco temporário não fica para trás.
        left = subprocess.run(["psql", admin, "-Atc", "SELECT count(*) FROM pg_database WHERE datname LIKE 'restore_check_%'"],
                              capture_output=True, text=True)
        assert left.stdout.strip() == "0"

    def test_ciclo_completo_dump_criptografado_e_restore(self, app, urls, tmp_path):
        source, admin = urls
        keyfile = tmp_path / "chave.txt"
        gen = subprocess.run(["age-keygen", "-o", str(keyfile)], capture_output=True, text=True)
        assert gen.returncode == 0
        public = next(line.split()[-1] for line in keyfile.read_text().splitlines() if line.startswith("# public key:"))
        out = tmp_path / "saida"
        dump = run(DUMP, env={"DATABASE_URL": source, "BACKUP_AGE_RECIPIENT": public, "BACKUP_DRY_RUN": "1", "BACKUP_OUT_DIR": str(out)})
        assert dump.returncode == 0, dump.stderr
        (arquivo,) = out.glob("controle-*.dump.age")
        # Cifrado de verdade: não é um dump legível.
        assert not arquivo.read_bytes().startswith(b"PGDMP")
        assert (out / f"{arquivo.name}.sha256").exists()
        restore = run(
            CHECK,
            "--dump", str(arquivo), "--sem-fonte",
            env={"AGE_IDENTITY_FILE": str(keyfile), "RESTORE_ADMIN_URL": admin},
        )
        assert restore.returncode == 0, restore.stdout + restore.stderr
        assert "RESULTADO: OK" in restore.stdout

    def test_arquivo_adulterado_e_recusado(self, app, urls, tmp_path):
        source, admin = urls
        keyfile = tmp_path / "chave.txt"
        subprocess.run(["age-keygen", "-o", str(keyfile)], capture_output=True, check=True)
        public = next(line.split()[-1] for line in keyfile.read_text().splitlines() if line.startswith("# public key:"))
        out = tmp_path / "saida"
        assert run(DUMP, env={"DATABASE_URL": source, "BACKUP_AGE_RECIPIENT": public, "BACKUP_DRY_RUN": "1", "BACKUP_OUT_DIR": str(out)}).returncode == 0
        (arquivo,) = out.glob("controle-*.dump.age")
        with arquivo.open("ab") as fh:
            fh.write(b"x")  # o .sha256 gravado no backup já não confere
        restore = run(CHECK, "--dump", str(arquivo), "--sem-fonte", env={"AGE_IDENTITY_FILE": str(keyfile), "RESTORE_ADMIN_URL": admin})
        assert restore.returncode == 4 and "sha256" in restore.stderr


# ------------------------------------------------------------------ envio, retenção e espelho de fotos (aws falso)

FAKE_AWS = r'''#!/usr/bin/env python3
"""aws falso: buckets são pastas em $FAKE_S3_ROOT. Só o que os scripts de backup usam."""
import os, shutil, sys
from pathlib import Path

root = Path(os.environ["FAKE_S3_ROOT"])
args = sys.argv[1:]
flags = {"dryrun": False, "delete": False}
clean, i = [], 0
while i < len(args):
    a = args[i]
    if a == "--endpoint-url":
        i += 2
        continue
    if a in ("--only-show-errors", "--recursive", "--summarize"):
        i += 1
        continue
    if a == "--dryrun":
        flags["dryrun"] = True
    elif a == "--delete":
        flags["delete"] = True
    else:
        clean.append(a)
    i += 1
sub = clean[0]

def split(uri):
    bucket, _, key = uri[len("s3://"):].partition("/")
    return bucket, key

def files(bucket, prefix=""):
    base = root / bucket
    return sorted(str(p.relative_to(base)) for p in base.rglob("*") if p.is_file() and str(p.relative_to(base)).startswith(prefix))

if sub == "s3api":
    opts = dict(zip(clean[2::2], clean[3::2]))
    keys = files(opts["--bucket"], opts.get("--prefix", ""))
    print("\t".join(keys) if keys else "None")
elif sub == "s3":
    op = clean[1]
    if op == "cp":
        src, dst = clean[2], clean[3]
        bucket, key = split(dst)
        target = root / bucket / key
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(src, target)
    elif op == "rm":
        bucket, key = split(clean[2])
        (root / bucket / key).unlink(missing_ok=True)
    elif op == "ls":
        bucket, key = split(clean[2])
        print("Total Objects: %d" % len(files(bucket, key)))
    elif op == "sync":
        sb, sk = split(clean[2]); db, dk = split(clean[3])
        src = {k[len(sk):]: k for k in files(sb, sk)}
        dst = {k[len(dk):]: k for k in files(db, dk)}
        if not flags["dryrun"]:
            for rel, k in src.items():
                t = root / db / (dk + rel); t.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(root / sb / k, t)
            if flags["delete"]:
                for rel, k in dst.items():
                    if rel not in src:
                        (root / db / k).unlink()
'''


@pytest.fixture()
def fake_aws(tmp_path):
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    aws = bin_dir / "aws"
    aws.write_text(FAKE_AWS)
    aws.chmod(0o755)
    root = tmp_path / "s3"
    root.mkdir()
    return {"PATH": f"{bin_dir}{os.pathsep}{os.environ['PATH']}", "FAKE_S3_ROOT": str(root)}, root


S3_ENV = {
    "BACKUP_S3_ENDPOINT": "https://conta.r2.cloudflarestorage.com",
    "BACKUP_S3_BUCKET": "backup",
    "BACKUP_S3_ACCESS_KEY_ID": "id",
    "BACKUP_S3_SECRET_ACCESS_KEY": "segredo-do-backup",
}


def _foto(root: Path, bucket: str, name: str, prefix: str = "") -> None:
    path = root / bucket / prefix / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(b"jpeg")


class TestEspelhoDeFotos:
    def env(self, fake, **extra):
        env, _ = fake
        return {**env, **S3_ENV, "PHOTOS_SRC_BUCKET": "fotos", **extra}

    def test_espelha_novas_e_apaga_o_que_saiu_da_origem(self, fake_aws):
        _, root = fake_aws
        _foto(root, "fotos", "empresa-a/fotos/1.jpg")
        _foto(root, "fotos", "empresa-a/fotos/2.jpg")
        _foto(root, "backup", "empresa-a/fotos/velha.jpg", "fotos/atual")
        result = run(SCRIPTS / "backup_photos.sh", env=self.env(fake_aws))
        assert result.returncode == 0, result.stderr
        copiados = sorted(p.relative_to(root / "backup").as_posix() for p in (root / "backup").rglob("*") if p.is_file())
        assert copiados == ["fotos/atual/empresa-a/fotos/1.jpg", "fotos/atual/empresa-a/fotos/2.jpg"]
        assert "segredo-do-backup" not in result.stdout + result.stderr

    def test_trava_quando_a_origem_aparece_vazia(self, fake_aws):
        _, root = fake_aws
        (root / "fotos").mkdir()
        _foto(root, "backup", "empresa-a/fotos/1.jpg", "fotos/atual")
        result = run(SCRIPTS / "backup_photos.sh", env=self.env(fake_aws))
        assert result.returncode == 6
        assert (root / "backup" / "fotos/atual/empresa-a/fotos/1.jpg").exists()

    def test_dry_run_nao_altera_nada(self, fake_aws):
        _, root = fake_aws
        _foto(root, "fotos", "a/fotos/1.jpg")
        result = run(SCRIPTS / "backup_photos.sh", env=self.env(fake_aws, BACKUP_DRY_RUN="1"))
        assert result.returncode == 0
        assert not (root / "backup").exists() or not any((root / "backup").rglob("*.jpg"))

    def test_recusa_origem_igual_ao_destino_e_endpoint_http(self, fake_aws):
        assert run(SCRIPTS / "backup_photos.sh", env=self.env(fake_aws, PHOTOS_SRC_BUCKET="backup")).returncode == 2
        assert run(SCRIPTS / "backup_photos.sh", env=self.env(fake_aws, BACKUP_S3_ENDPOINT="http://x")).returncode == 2

    def test_backup_run_chama_dump_e_fotos_e_propaga_falha(self, fake_aws):
        # Sem DATABASE_URL o dump falha (2); as fotos ainda rodam e o código final é diferente de zero.
        _, root = fake_aws
        _foto(root, "fotos", "a/fotos/1.jpg")
        result = run(SCRIPTS / "backup_run.sh", env=self.env(fake_aws))
        assert result.returncode != 0
        assert (root / "backup" / "fotos/atual/a/fotos/1.jpg").exists()


@requires_postgres
@requires_tools
class TestEnvioERetencao:
    @pytest.fixture()
    def ctx(self, app, fake_aws, tmp_path):
        keyfile = tmp_path / "chave.txt"
        subprocess.run(["age-keygen", "-o", str(keyfile)], capture_output=True, check=True)
        public = next(line.split()[-1] for line in keyfile.read_text().splitlines() if line.startswith("# public key:"))
        env, root = fake_aws
        return {
            **env,
            **S3_ENV,
            "DATABASE_URL": libpq(get_test_database_url()),
            "BACKUP_AGE_RECIPIENT": public,
        }, root, keyfile

    def test_envia_dump_criptografado_e_aplica_retencao_com_minimo(self, ctx):
        env, root, _ = ctx
        for day in ("20200101", "20200102", "20200103", "20200104", "20200105"):
            _foto(root, "backup", f"controle-{day}T060000Z.dump.age", "db")
            _foto(root, "backup", f"controle-{day}T060000Z.dump.age.sha256", "db")
        recente = "controle-29990101T000000Z.dump.age"
        _foto(root, "backup", recente, "db")
        result = run(DUMP, env={**env, "BACKUP_RETENTION_DAYS": "30", "BACKUP_MIN_KEEP": "3"})
        assert result.returncode == 0, result.stderr
        objetos = sorted(p.name for p in (root / "backup" / "db").iterdir() if p.name.endswith(".dump.age"))
        # 5 antigos + 1 futuro + o novo = 7: a retenção apaga os mais antigos até restarem
        # BACKUP_MIN_KEEP (3); sobra o mais novo dos antigos, o "futuro" e o novo.
        assert len(objetos) == 3 and recente in objetos
        assert "controle-20200105T060000Z.dump.age" in objetos
        assert not any(n.startswith(("controle-20200101", "controle-20200102")) for n in objetos)
        novo = [n for n in objetos if n not in {recente, "controle-20200105T060000Z.dump.age"}]
        assert len(novo) == 1 and (root / "backup" / "db" / (novo[0] + ".sha256")).exists()
        assert not (root / "backup" / "db" / "controle-20200101T060000Z.dump.age.sha256").exists()
        # O que foi para o bucket é texto cifrado e as credenciais não aparecem na saída.
        assert not (root / "backup" / "db" / novo[0]).read_bytes().startswith(b"PGDMP")
        assert "segredo-do-backup" not in result.stdout + result.stderr

    def test_minimo_impede_apagar_tudo(self, ctx):
        env, root, _ = ctx
        for day in ("20200101", "20200102"):
            _foto(root, "backup", f"controle-{day}T060000Z.dump.age", "db")
        result = run(DUMP, env={**env, "BACKUP_RETENTION_DAYS": "1", "BACKUP_MIN_KEEP": "3"})
        assert result.returncode == 0, result.stderr
        objetos = [p.name for p in (root / "backup" / "db").iterdir() if p.name.endswith(".dump.age")]
        assert len(objetos) == 3  # 2 antigos preservados + o novo

    def test_o_dump_enviado_restaura(self, ctx, app):
        env, root, keyfile = ctx
        assert run(DUMP, env=env).returncode == 0
        (arquivo,) = [p for p in (root / "backup" / "db").iterdir() if p.name.endswith(".dump.age")]
        admin = os.environ.get("RESTORE_CHECK_ADMIN_URL") or libpq(get_test_database_url(), "postgres")
        probe = subprocess.run(["psql", admin, "-Atc", "SELECT rolcreatedb OR rolsuper FROM pg_roles WHERE rolname=current_user"], capture_output=True, text=True)
        if probe.stdout.strip() != "t":
            pytest.skip("sem CREATE DATABASE no servidor de teste")
        restore = run(CHECK, "--dump", str(arquivo), "--sem-fonte", env={"AGE_IDENTITY_FILE": str(keyfile), "RESTORE_ADMIN_URL": admin})
        assert restore.returncode == 0, restore.stdout + restore.stderr
