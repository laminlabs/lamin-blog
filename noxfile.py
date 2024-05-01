import nox
from pathlib import Path
from laminci import move_built_docs_to_slash_project_slug
from laminci.nox import run_pre_commit

nox.options.default_venv_backend = "none"


@nox.session
def lint(session: nox.Session) -> None:
    run_pre_commit(session)


@nox.session
def build(session: nox.Session):
    prefix = "." if Path("./lndocs").exists() else ".."
    if nox.options.default_venv_backend == "none":
        session.run(*f"uv pip install --system {prefix}/lndocs".split())
    else:
        session.install(f"{prefix}/lndocs")

    session.run(*["lndocs", "--strict"])
    move_built_docs_to_slash_project_slug()
