import nox
import tempfile

nox.options.sessions = "lint", "mypy", "tests"

python_version = ["3.8"]

typecheck_locations = ("misc_crypto",)
lint_locations = typecheck_locations + ("tests", "noxfile.py")


@nox.session(python=python_version)
def lint(session):
    args = session.posargs or lint_locations
    install_with_constraints(
        session,
        "flake8",
        "flake8-black",
        "flake8-import-order",
    )
    session.run("flake8", *args)


@nox.session(python=python_version)
def mypy(session):
    args = session.posargs or typecheck_locations
    session.run("poetry", "install", external=True)
    session.run("mypy", *args)


@nox.session(python=python_version)
def black(session):
    args = session.posargs or lint_locations
    install_with_constraints(session, "black")
    session.run("black", *args)


@nox.session(python=python_version)
def tests(session):
    session.run("poetry", "install", external=True)
    session.run("pytest")


def install_with_constraints(session, *args, **kwargs):
    with tempfile.NamedTemporaryFile() as requirements:
        session.run(
            "poetry",
            "export",
            "--dev",
            "--without-hashes",
            "--format=requirements.txt",
            f"--output={requirements.name}",
            external=True,
        )
        session.install(f"--constraint={requirements.name}", *args, **kwargs)
