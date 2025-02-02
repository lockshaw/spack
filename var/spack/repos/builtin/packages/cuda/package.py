# Copyright 2013-2021 Lawrence Livermore National Security, LLC and other
# Spack Project Developers. See the top-level COPYRIGHT file for details.
#
# SPDX-License-Identifier: (Apache-2.0 OR MIT)

from spack import *
from glob import glob
from llnl.util.filesystem import LibraryList, copy_tree
import os
import re
import platform
import llnl.util.tty as tty

# FIXME Remove hack for polymorphic versions
# This package uses a ugly hack to be able to dispatch, given the same
# version, to different binary packages based on the platform that is
# running spack. See #13827 for context.
# If you need to add a new version, please be aware that:
#  - versions in the following dict are automatically added to the package
#  - version tuple must be in the form (checksum, url)
#  - checksum must be sha256
#  - package key must be in the form '{os}-{arch}' where 'os' is in the
#    format returned by platform.system() and 'arch' by platform.machine()

_versions = {
    '11.2.1': {
        'Linux-aarch64': ('4b322fa6477d1a2cd2f2f526fa520c0f90bef2c264ef8435cb016bebb5456c5e', 'https://developer.download.nvidia.com/compute/cuda/11.2.1/local_installers/cuda_11.2.1_460.32.03_linux_sbsa.run'),
        'Linux-x86_64': ('1da98cb897cc5f58a7445a4a66ca4f6926867706cb3af58a669cdcd8dc3d17c8', 'https://developer.download.nvidia.com/compute/cuda/11.2.1/local_installers/cuda_11.2.1_460.32.03_linux.run'),
        'Linux-ppc64le': ('b3e8b6cd76872deb3acd050d32e197bc1c655e142b169070f0f9753680461a3f', 'https://developer.download.nvidia.com/compute/cuda/11.2.1/local_installers/cuda_11.2.1_460.32.03_linux_ppc64le.run')},
    '11.2.0': {
        'Linux-aarch64': ('c11dc274660e9b47b0f25ca66861a7406246a7191f1b04d0710515fcac0fa6cd', 'https://developer.download.nvidia.com/compute/cuda/11.2.0/local_installers/cuda_11.2.0_460.27.04_linux_sbsa.run'),
        'Linux-x86_64': ('9c50283241ac325d3085289ed9b9c170531369de41165ce271352d4a898cbdce', 'https://developer.download.nvidia.com/compute/cuda/11.2.0/local_installers/cuda_11.2.0_460.27.04_linux.run'),
        'Linux-ppc64le': ('adc3267df5dbfdaf51cb4c9b227ba6bfd979a39d9b4136bba0eba6b1dd2a2731', 'https://developer.download.nvidia.com/compute/cuda/11.2.0/local_installers/cuda_11.2.0_460.27.04_linux_ppc64le.run')},
    '11.1.1': {
        'Linux-aarch64': ('9ab1dbafba205c06bea8c88e38cdadb3038af19cb56e7b3ba734d3d7a84b8f02', 'https://developer.download.nvidia.com/compute/cuda/11.1.1/local_installers/cuda_11.1.1_455.32.00_linux_sbsa.run'),
        'Linux-x86_64': ('3eae6727086024925ebbcef3e9a45ad379d8490768fd00f9c2d8b6fd9cd8dd8f', 'https://developer.download.nvidia.com/compute/cuda/11.1.1/local_installers/cuda_11.1.1_455.32.00_linux.run'),
        'Linux-ppc64le': ('023e571fe26ee829c98138dfc305a92279854aac7d184d255fd58c06c6af3c17', 'https://developer.download.nvidia.com/compute/cuda/11.1.1/local_installers/cuda_11.1.1_455.32.00_linux_ppc64le.run')},
    '11.1.0': {
        'Linux-aarch64': ('878cbd36c5897468ef28f02da50b2f546af0434a8a89d1c724a4d2013d6aa993', 'https://developer.download.nvidia.com/compute/cuda/11.1.0/local_installers/cuda_11.1.0_455.23.05_linux_sbsa.run'),
        'Linux-x86_64': ('858cbab091fde94556a249b9580fadff55a46eafbcb4d4a741d2dcd358ab94a5', 'https://developer.download.nvidia.com/compute/cuda/11.1.0/local_installers/cuda_11.1.0_455.23.05_linux.run'),
        'Linux-ppc64le': ('a561e6f7f659bc4100e4713523b0b8aad6b36aa77fac847f6423e7780c750064', 'https://developer.download.nvidia.com/compute/cuda/11.1.0/local_installers/cuda_11.1.0_455.23.05_linux_ppc64le.run')},
    '11.0.2': {
        'Linux-aarch64': ('23851e30f7c47a1baad92891abde0adbc783de5962c7480b9725198ceacda4a0', 'https://developer.download.nvidia.com/compute/cuda/11.0.2/local_installers/cuda_11.0.2_450.51.05_linux_sbsa.run'),
        'Linux-x86_64': ('48247ada0e3f106051029ae8f70fbd0c238040f58b0880e55026374a959a69c1', 'https://developer.download.nvidia.com/compute/cuda/11.0.2/local_installers/cuda_11.0.2_450.51.05_linux.run'),
        'Linux-ppc64le': ('db06d0f3fbf6f7aa1f106fc921ad1c86162210a26e8cb65b171c5240a3bf75da', 'https://developer.download.nvidia.com/compute/cuda/11.0.2/local_installers/cuda_11.0.2_450.51.05_linux_ppc64le.run')},
    '10.2.89': {
        'Linux-x86_64': ('560d07fdcf4a46717f2242948cd4f92c5f9b6fc7eae10dd996614da913d5ca11', 'https://developer.download.nvidia.com/compute/cuda/10.2/Prod/local_installers/cuda_10.2.89_440.33.01_linux.run'),
        'Linux-ppc64le': ('5227774fcb8b10bd2d8714f0a716a75d7a2df240a9f2a49beb76710b1c0fc619', 'https://developer.download.nvidia.com/compute/cuda/10.2/Prod/local_installers/cuda_10.2.89_440.33.01_linux_ppc64le.run')},
    '10.1.243': {
        'Linux-x86_64': ('e7c22dc21278eb1b82f34a60ad7640b41ad3943d929bebda3008b72536855d31', 'https://developer.download.nvidia.com/compute/cuda/10.1/Prod/local_installers/cuda_10.1.243_418.87.00_linux.run'),
        'Linux-ppc64le': ('b198002eef010bab9e745ae98e47567c955d00cf34cc8f8d2f0a6feb810523bf', 'https://developer.download.nvidia.com/compute/cuda/10.1/Prod/local_installers/cuda_10.1.243_418.87.00_linux_ppc64le.run')},
    '10.0.130': {
        'Linux-x86_64': ('92351f0e4346694d0fcb4ea1539856c9eb82060c25654463bfd8574ec35ee39a', 'https://developer.nvidia.com/compute/cuda/10.0/Prod/local_installers/cuda_10.0.130_410.48_linux')},
    '9.2.88': {
        'Linux-x86_64': ('8d02cc2a82f35b456d447df463148ac4cc823891be8820948109ad6186f2667c', 'https://developer.nvidia.com/compute/cuda/9.2/Prod/local_installers/cuda_9.2.88_396.26_linux')},
    '9.1.85': {
        'Linux-x86_64': ('8496c72b16fee61889f9281449b5d633d0b358b46579175c275d85c9205fe953', 'https://developer.nvidia.com/compute/cuda/9.1/Prod/local_installers/cuda_9.1.85_387.26_linux')},
    '9.0.176': {
        'Linux-x86_64': ('96863423feaa50b5c1c5e1b9ec537ef7ba77576a3986652351ae43e66bcd080c', 'https://developer.nvidia.com/compute/cuda/9.0/Prod/local_installers/cuda_9.0.176_384.81_linux-run')},
    '8.0.61': {
        'Linux-x86_64': ('9ceca9c2397f841024e03410bfd6eabfd72b384256fbed1c1e4834b5b0ce9dc4', 'https://developer.nvidia.com/compute/cuda/8.0/Prod2/local_installers/cuda_8.0.61_375.26_linux-run')},
    '8.0.44': {
        'Linux-x86_64': ('64dc4ab867261a0d690735c46d7cc9fc60d989da0d69dc04d1714e409cacbdf0', 'https://developer.nvidia.com/compute/cuda/8.0/prod/local_installers/cuda_8.0.44_linux-run')},
    '7.5.18': {
        'Linux-x86_64': ('08411d536741075131a1858a68615b8b73c51988e616e83b835e4632eea75eec', 'http://developer.download.nvidia.com/compute/cuda/7.5/Prod/local_installers/cuda_7.5.18_linux.run')},
    '6.5.14': {
        'Linux-x86_64': ('f3e527f34f317314fe8fcd8c85f10560729069298c0f73105ba89225db69da48', 'http://developer.download.nvidia.com/compute/cuda/6_5/rel/installers/cuda_6.5.14_linux_64.run')},
}


class Cuda(Package):
    """CUDA is a parallel computing platform and programming model invented
    by NVIDIA. It enables dramatic increases in computing performance by
    harnessing the power of the graphics processing unit (GPU).

    Note: This package does not currently install the drivers necessary
    to run CUDA. These will need to be installed manually. See:
    https://docs.nvidia.com/cuda/ for details."""

    homepage = "https://developer.nvidia.com/cuda-zone"

    maintainers = ['ax3l', 'Rombur']
    executables = ['^nvcc$']

    for ver, packages in _versions.items():
        key = "{0}-{1}".format(platform.system(), platform.machine())
        pkg = packages.get(key)
        if pkg:
            version(ver, sha256=pkg[0], url=pkg[1], expand=False)

    # macOS Mojave drops NVIDIA graphics card support -- official NVIDIA
    # drivers do not exist for Mojave. See
    # https://devtalk.nvidia.com/default/topic/1043070/announcements/faq-about-macos-10-14-mojave-nvidia-drivers/
    # Note that a CUDA Toolkit installer does exist for macOS Mojave at
    # https://developer.nvidia.com/compute/cuda/10.1/Prod1/local_installers/cuda_10.1.168_mac.dmg,
    # but support for Mojave is dropped in later versions, and none of the
    # macOS NVIDIA drivers at
    # https://www.nvidia.com/en-us/drivers/cuda/mac-driver-archive/ mention
    # Mojave support -- only macOS High Sierra 10.13 is supported.
    conflicts('arch=darwin-mojave-x86_64')

    depends_on('libxml2', when='@10.1.243:')

    provides('opencl@:1.2', when='@7:')
    provides('opencl@:1.1', when='@:6')

    @classmethod
    def determine_version(cls, exe):
        output = Executable(exe)('--version', output=str, error=str)
        match = re.search(r'Cuda compilation tools, release .*?, V(\S+)',
                          output)
        return match.group(1) if match else None

    def setup_build_environment(self, env):
        if self.spec.satisfies('@10.1.243:'):
            libxml2_home = self.spec['libxml2'].prefix
            env.set('LIBXML2HOME', libxml2_home)
            env.append_path('LD_LIBRARY_PATH', libxml2_home.lib)

    def setup_dependent_build_environment(self, env, dependent_spec):
        env.set('CUDAHOSTCXX', dependent_spec.package.compiler.cxx)

    def setup_run_environment(self, env):
        env.set('CUDA_HOME', self.prefix)

    def install(self, spec, prefix):
        if os.path.exists('/tmp/cuda-installer.log'):
            try:
                os.remove('/tmp/cuda-installer.log')
            except OSError:
                if spec.satisfies('@10.1:'):
                    tty.die("The cuda installer will segfault due to the "
                            "presence of /tmp/cuda-installer.log "
                            "please remove the file and try again ")
        runfile = glob(join_path(self.stage.source_path, 'cuda*_linux*'))[0]

        # Note: NVIDIA does not officially support many newer versions of
        # compilers.  For example, on CentOS 6, you must use GCC 4.4.7 or
        # older. See:
        # http://docs.nvidia.com/cuda/cuda-installation-guide-linux/#system-requirements
        # https://gist.github.com/ax3l/9489132
        # for details.

        # CUDA 10.1 on ppc64le fails to copy some files, the workaround is adapted from
        # https://forums.developer.nvidia.com/t/cuda-10-1-243-10-1-update-2-ppc64le-run-file-installation-issue/82433
        # See also #21170
        if spec.satisfies('@10.1.243') and platform.machine() == 'ppc64le':
            includedir = "targets/ppc64le-linux/include"
            os.makedirs(os.path.join(prefix, includedir))
            os.makedirs(os.path.join(prefix, "src"))
            os.symlink(includedir, os.path.join(prefix, "include"))

        # CUDA 10.1+ has different cmdline options for the installer
        arguments = [
            runfile,            # the install script
            '--silent',         # disable interactive prompts
            '--override',       # override compiler version checks
            '--toolkit',        # install CUDA Toolkit
        ]
        if spec.satisfies('@10.1:'):
            arguments.append('--installpath=%s' % prefix)   # Where to install
        else:
            arguments.append('--verbose')                   # Verbose log file
            arguments.append('--toolkitpath=%s' % prefix)   # Where to install
        install_shell = which('sh')
        install_shell(*arguments)
        try:
            os.remove('/tmp/cuda-installer.log')
        except OSError:
            pass

        # Environment views do not currently support symlinks.
        # Since the include/ and lib64/ directories in cuda are
        # symlinks to subdirectories of targets/ and thus do
        # not appear in the view, we manually replace them with
        # copies of the directories they point to.
        # For reference, see https://github.com/spack/spack/issues/19531
        include_dir = join_path(prefix, 'include')
        pointing_to = join_path(prefix, os.readlink(include_dir))
        os.remove(include_dir)
        copy_tree(pointing_to, include_dir)

        lib64_dir = join_path(prefix, 'lib64')
        pointing_to = join_path(prefix, os.readlink(lib64_dir))
        os.remove(lib64_dir)
        copy_tree(pointing_to, lib64_dir)

    @property
    def libs(self):
        libs = find_libraries('libcudart', root=self.prefix, shared=True,
                              recursive=True)

        filtered_libs = []
        # CUDA 10.0 provides Compatability libraries for running newer versions
        # of CUDA with older drivers. These do not work with newer drivers.
        for lib in libs:
            parts = lib.split(os.sep)
            if 'compat' not in parts and 'stubs' not in parts:
                filtered_libs.append(lib)
        return LibraryList(filtered_libs)
