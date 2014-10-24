import StringIO
import compileall
import contextlib
import os
import pathlib
import requests
import shutil
import subprocess
import tempfile
import zipfile

from django.conf import settings

extract_path = pathlib.Path(settings.BASE_DIR) / "build"


def download_and_extract_zip(branch):
    try:
        extract_path.mkdir()
    except OSError:
        pass

    url = "https://github.com/learningequality/ka-lite/archive/{}.zip".format(branch)

    response = requests.get(url)
    response.raise_for_status()

    f = StringIO.StringIO(response.content)
    zip = zipfile.ZipFile(f)

    zip.extractall(str(extract_path))


@contextlib.contextmanager
def inside_kalite_directory(branch_or_directory):
    old_cwd = pathlib.Path('.')
    if pathlib.Path(branch_or_directory).exists():  # is a directory
        kalite_path = pathlib.Path(branch_or_directory)
    else:
        kalite_path = (extract_path /
                       "ka-lite-{}".format(branch_or_directory) /
                       "kalite")

    os.chdir(str(kalite_path))

    yield kalite_path

    os.chdir(str(old_cwd))


def insert_dummy_fle_utils_testing_file(dir):
    with inside_kalite_directory(dir) as kalite_path:
        target_path = (kalite_path /
                       ".." /
                       "python-packages" /
                       "fle_utils" /
                       "testing")

        try:
            target_path.mkdir()
        except OSError:
            pass

        src = pathlib.Path(settings.BASE_DIR) / "files" / "dummy_decorators.py"
        dest = target_path / "decorators.py"

        shutil.copy(str(src), str(dest))



def mark_as_built(dir):
    with inside_kalite_directory(dir) as kalite_path:
        build_indicator_file = kalite_path / "_built.touch"
        build_indicator_file.touch()


def generate_pyo_files(dir):
    with inside_kalite_directory(dir):
        compileall.compile_dir(str(dir))
        compileall.compile_file(str(dir / "manage.py"))  # somehow we need to compile this manually


@contextlib.contextmanager
def temp_kalite_directory(dir_to_copy):
    dir_to_copy = pathlib.Path(dir_to_copy)
    dest_dir = pathlib.Path(tempfile.mkdtemp())
    temp_kalite_dir = dest_dir / "ka-lite"

    shutil.copytree(str(dir_to_copy), str(temp_kalite_dir))

    yield temp_kalite_dir / "kalite"

    shutil.rmtree(str(dest_dir))


def call_command(branch_or_directory, command):
    with inside_kalite_directory(branch_or_directory):
        env = os.environ.copy()
        env["DJANGO_SETTINGS_MODULE"] = "kalite.settings"

        command += ["--traceback"]

        out = subprocess.check_output(["python", "manage.py"] + command,
                                      env=env)
        return out


def collectstatic(branch_or_directory):
    with inside_kalite_directory(branch_or_directory) as kalite_path:
        command = ["collectstatic", "--noinput"]
        call_command(kalite_path, command)


def delete_blacklisted_files(branch_or_directory, removejuststatic=False):
    with inside_kalite_directory(branch_or_directory) as kalite_path:
        # make manage.py executable first
        managepy = kalite_path / "manage.py"
        managepy.chmod(0o755)

        command = ["generate_blacklist",
                   "--removekhan",
                   "--removei18n",
                   "--removeunused",
                   # "--removetests"
        ]

        if removejuststatic:
            command = ["generate_blacklist", "--removestatic"]

        out = (call_command(kalite_path, command).splitlines())

        for path_to_delete in out:
            path_to_delete = pathlib.Path(path_to_delete)
            if not path_to_delete.exists():
                print "{} deleted already!".format(str(path_to_delete))
            else:
                try:
                    path_to_delete.unlink()
                except OSError:
                    os.system("rm -rf %s"  % str(path_to_delete))
                print "{} deleted!".format(str(path_to_delete))


def delete_py_files(dir):
    with inside_kalite_directory(dir) as kalite_path:
        root = kalite_path.parent

        for pyfile in root.rglob("*.py"):
            # don't delete any settings file, btw
            if not "settings.py" in str(pyfile):
                pyfile.unlink()
