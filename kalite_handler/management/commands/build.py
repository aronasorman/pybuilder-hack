import pathlib
from optparse import make_option

from django.conf import settings
from django.core.management.base import NoArgsCommand

from kalite_handler import lib


def build_kalite(target):
    print "Marking the directory as built by the build process"
    lib.mark_as_built(target)

    print "Generating pyo files"
    lib.generate_pyo_files(target)

    print "disabling i18n"
    lib.append_to_local_settings(target, "USE_I18N = False")
    lib.append_to_local_settings(target, "USE_L10N = False")

    print "Disable DEBUG mode"
    lib.append_to_local_settings(target, "DEBUG = False")

    print "Deleting some blacklisted files"
    lib.delete_blacklisted_files(target)

    print "Collecting static files"
    lib.collectstatic(target)

    print "Deleting extra static files"
    lib.delete_blacklisted_files(target, removejuststatic=True)

    # Django doesn't like deleted py files. Have to investigate more
    # print "Deleting the .py files"
    # lib.delete_py_files(target)

    print "Zipping up everything"
    outpath = pathlib.Path(settings.BASE_DIR) / "kalite"
    # zip up the tmp directory by getting kalite's grandparent
    lib.zip_directory(target.parent.parent, out=outpath)


class Command(NoArgsCommand):
    option_list = NoArgsCommand.option_list + (
        make_option("--branch", "-b",
                    action="store",
                    dest="branch",
                    help="branch or commit to download from KA Lite"),
        make_option("--directory", "-d",
                    action="store",
                    dest="directory",
                    help="the directory to build from")
    )

    def handle(*args, **kwargs):

        if kwargs["branch"]:
            build_kalite(kwargs["branch"])
        elif kwargs["directory"]:
            assert pathlib.Path(kwargs["directory"]).exists(), "given path does not exist"

            with lib.temp_kalite_directory(kwargs["directory"]) as dir:
                build_kalite(dir)
