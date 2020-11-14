import json
from collections import OrderedDict
import subprocess
import os
import urllib.request
from .logger import getLogger
from typing import List, Tuple
import sys
import zipfile
import itertools

log = getLogger()


SCRIPT_DIR = os.path.dirname(os.path.realpath(__file__))
SCRIPT_NAME = os.path.basename(__file__)


def scala_install_dir(path):
    return str(path / "scala")


def ivy_cache_dir(path):
    return str(path / "ivycache")


def coursier_bin(install_dir):
    return "{}/coursier".format(install_dir)


def ivy_deps_file(directory):
    return "{}/ivydependencies.json".format(directory)


def scala_version_dep(version):
    return "org.scala-lang:scala-compiler:{}".format(version)


def make_jar(jarfile: str, dirs: List[str]) -> None:
    """
    This function crates reproducible jars
    The jar command includes the Date and platform-specific file attribute information
    """
    with zipfile.ZipFile(jarfile, 'w', zipfile.ZIP_DEFLATED) as zip:
        written = set()
        for dir in dirs:
            for root, ds, files in os.walk(dir):
                for f in itertools.chain(ds, files):
                    abspath = os.path.join(root, f)
                    relpath = os.path.relpath(abspath, dir)
                    # https://stackoverflow.com/questions/434641#6297838
                    # Note the default time for ZipInfo is 1 Jan 1980
                    if os.path.isfile(abspath):
                        assert relpath not in written, \
                            "Attempting to jar duplicate filename {}".format(relpath)
                        info = zipfile.ZipInfo(relpath)
                        info.external_attr = 0o664 << 16 # -rw-rw-r--
                        bytes = open(abspath, 'rb').read()
                        zip.writestr(info, bytes, zipfile.ZIP_DEFLATED)
                    elif os.path.isdir(abspath):
                        # Duplicate directories are fine
                        if relpath not in written:
                            info = zipfile.ZipInfo(relpath + '/')
                            info.external_attr = 0o40775 << 16 # drwxrwxr-x
                            info.external_attr |= 0x10 # MS-DOS directory flag
                            zip.writestr(info, '', zipfile.ZIP_STORED)
                    else:
                        raise Exception("Unexpected non-file and non-dir path {}".format(abspath))
                    written.add(relpath)


def calc_sha256(filename):
    import hashlib
    block_size = 65536
    hasher = hashlib.sha256()
    with open(filename, 'rb') as f:
        buf = f.read(block_size)
        while len(buf) > 0:
            hasher.update(buf)
            buf = f.read(block_size)
    return hasher.hexdigest()


def _fetch_and_check_file(filename, url, expected_sha256):
    print("Downloading from {}".format(url))
    urllib.request.urlretrieve(url, filename)

    actual_sha256 = calc_sha256(filename)
    if actual_sha256 != expected_sha256:
        msg = "Error! SHA256 mismatch for {}!".format(filename)
        suggestion = "Please delete the 'scala/' directory and re-run!"
        extra_info = "  Expected: {}\n  Got:      {}".format(expected_sha256, actual_sha256)
        raise Exception("{} {}\n{}".format(msg, suggestion, extra_info))

    os.chmod(filename, 0o755)


def install_coursier(install_dir, jar=False):
    release_host = "https://github.com/coursier/coursier/releases/download"
    version = "v2.0.5"

    platform = sys.platform
    # https://docs.python.org/3.5/library/platform.html#platform.architecture
    is_64bit = sys.maxsize > 2**32

    name = ""
    sha256 = None
    if platform == 'darwin' and is_64bit and not jar:
        name = "cs-x86_64-apple-darwin"
        sha256 = "89a2ed25a42073c5d9425623fec7b09b1edbcdf7c2fdf8080d0dffcf0e85297a"
    elif platform == 'linux' and is_64bit and not jar:
        name = "cs-x86_64-pc-linux"
        sha256 = "d29ed1d8b5694b2e9f8138a57a7b7236b076640ad7cab8c35a9e419bb5ac4c2b"
    else:
        name = "coursier.jar"
        sha256 = "59e5574d3ecd58ff8e808448dd2d6fcf02d161ec01b0a6f478f084410507ec41"

    url = '{}/{}/{}'.format(release_host, version, name)

    filename = coursier_bin(install_dir)

    _fetch_and_check_file(filename, url, sha256)


def split_scala_version(version):
    parts = version.split('.')
    if len(parts) != 3:
        raise Exception("Malformed Scala Version {}".format(version))
    if parts[0] != "2":
        raise Exception("Only Scala 2.X.Y are supported!")
    return parts


def get_major_version(version):
    return '.'.join(split_scala_version(version)[:2])


def unique_list(l):
    d = OrderedDict()
    for e in l:
        d[e] = None
    return list(d.keys())


# TODO More validation?
def expand_scala_dep(version, dep):
    parts = dep.split(':')

    def errMalformed():
        raise Exception("Malformed IvyDependency {}!".format(dep))

    def assertHasScala():
        if version is None:
            raise Exception("Must specify scalaVersion for IvyDependency {}!".format(dep))

    if len(parts) == 3:
        # Java dep
        return dep
    elif len(parts) == 4:
        # Scala Dep
        c = parts.pop(1)
        if c != '':
            errMalformed()
        assertHasScala()
        sv = split_scala_version(version)
        parts[1] = "{}_{}.{}".format(parts[1], sv[0], sv[1])
        return ':'.join(parts)
    elif len(parts) == 5:
        c = parts.pop(1)
        d = parts.pop(1)
        if c != '' or d != '':
            errMalformed()
        assertHasScala()
        parts[1] = "{}_{}".format(parts[1], version)
        return ':'.join(parts)
    else:
        errMalformed()


# TODO JSON validation/schema?
def read_ivy_file(json_file):
    data = json.load(json_file, object_pairs_hook=OrderedDict)
    # Ignore project names, could be duplicates?
    return list(data.values())


def filter_versions(allVers, myVers):
    """
    Determines what versions should be kept out of myVers based on major Scala version
    """
    majorVersions = set([get_major_version(ver) for ver in allVers])
    return [ver for ver in myVers if get_major_version(ver) in majorVersions]


def resolve_dependencies(projects: List[dict]) -> List[tuple]:
    """
    Determines which dependencies should be fetched
    crossScalaVersions are used to fetch extra versions if any project has a
    scalaVersion that matches the *major* version of the crossScalaVersion
    """
    scalaVersions = unique_list(filter(None, [proj.get('scalaVersion') for proj in projects]))
    dep_groups = []
    scala_versions = []
    for proj in projects:
        version = proj.get('scalaVersion')
        if version is not None:
            scala_versions.append(version)
        pdeps = proj.get('dependencies') or []
        crossVersions = proj.get('crossScalaVersions') or []
        # Note version can be none, this is okay
        allVersions = [version] + filter_versions(scalaVersions, crossVersions)
        for ver in allVersions:
            deps = [expand_scala_dep(ver, dep) for dep in pdeps]
            if ver is not None:
                deps.append("org.scala-lang:scala-library:{}".format(ver))
            dep_groups.append(tuple(deps))
    # Fetch the Scala compiler for each Scala version as well
    for ver in scala_versions:
        dep_groups.append(tuple(["org.scala-lang:scala-compiler:{}".format(ver)]))
    unique_groups = unique_list(dep_groups)
    return unique_groups


def fetch_ivy_deps(coursier: str, cache: str, deps: tuple) -> None:
    log.debug("Fetching [{}]...".format(", ".join(deps)))
    cmd = [coursier, "fetch", "--cache", cache] + list(deps)
    proc = subprocess.run(cmd)
    if proc.returncode != 0:
        raise Exception("Unable to fetch dependencies [{}]".format(", ".join(deps)))


def fetch_ivy_dependencies(dep_files, install_dir, ivy_cache_dir):
    coursier = coursier_bin(install_dir)

    projects = []
    for fh in dep_files:
        projects.extend(read_ivy_file(fh))

    dep_groups = resolve_dependencies(projects)

    for group in dep_groups:
        fetch_ivy_deps(coursier, ivy_cache_dir, group)
