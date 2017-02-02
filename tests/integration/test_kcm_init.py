# Intel License for KCM (version January 2017)
#
# Copyright (c) 2017 Intel Corporation.
#
# Use.  You may use the software (the "Software"), without modification,
# provided the following conditions are met:
#
# * Neither the name of Intel nor the names of its suppliers may be used to
#   endorse or promote products derived from this Software without specific
#   prior written permission.
# * No reverse engineering, decompilation, or disassembly of this Software
#   is permitted.
#
# Limited patent license.  Intel grants you a world-wide, royalty-free,
# non-exclusive license under patents it now or hereafter owns or controls to
# make, have made, use, import, offer to sell and sell ("Utilize") this
# Software, but solely to the extent that any such patent is necessary to
# Utilize the Software alone. The patent license shall not apply to any
# combinations which include this software.  No hardware per se is licensed
# hereunder.
#
# Third party and other Intel programs.  "Third Party Programs" are the files
# listed in the "third-party-programs.txt" text file that is included with the
# Software and may include Intel programs under separate license terms. Third
# Party Programs, even if included with the distribution of the Materials, are
# governed by separate license terms and those license terms solely govern your
# use of those programs.
#
# DISCLAIMER.  THIS SOFTWARE IS PROVIDED "AS IS" AND ANY EXPRESS OR IMPLIED
# WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES OF
# MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE, AND NON-INFRINGEMENT ARE
# DISCLAIMED. THIS SOFTWARE IS NOT INTENDED NOR AUTHORIZED FOR USE IN SYSTEMS
# OR APPLICATIONS WHERE FAILURE OF THE SOFTWARE MAY CAUSE PERSONAL INJURY OR
# DEATH.
#
# LIMITATION OF LIABILITY. IN NO EVENT WILL INTEL BE LIABLE FOR ANY DIRECT,
# INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
# (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
# LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND
# ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
# (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
# SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE. YOU AGREE TO
# INDEMNIFIY AND HOLD INTEL HARMLESS AGAINST ANY CLAIMS AND EXPENSES RESULTING
# FROM YOUR USE OR UNAUTHORIZED USE OF THE SOFTWARE.
#
# No support.  Intel may make changes to the Software, at any time without
# notice, and is not obligated to support, update or provide training for the
# Software.
#
# Termination. Intel may terminate your right to use the Software in the event
# of your breach of this Agreement and you fail to cure the breach within a
# reasonable period of time.
#
# Feedback.  Should you provide Intel with comments, modifications,
# corrections, enhancements or other input ("Feedback") related to the Software
# Intel will be free to use, disclose, reproduce, license or otherwise
# distribute or exploit the Feedback in its sole discretion without any
# obligations or restrictions of any kind, including without limitation,
# intellectual property rights or licensing obligations.
#
# Compliance with laws.  You agree to comply with all relevant laws and
# regulations governing your use, transfer, import or export (or prohibition
# thereof) of the Software.
#
# Governing law.  All disputes will be governed by the laws of the United
# States of America and the State of Delaware without reference to conflict of
# law principles and subject to the exclusive jurisdiction of the state or
# federal courts sitting in the State of Delaware, and each party agrees that
# it submits to the personal jurisdiction and venue of those courts and waives
# any objections. The United Nations Convention on Contracts for the
# International Sale of Goods (1980) is specifically excluded and will not
# apply to the Software.

from . import integration
from .. import helpers
from intel import proc, topology
import os
import pytest
import tempfile
import subprocess


# Physical CPU cores on the first socket.
cores = topology.parse(topology.lscpu())[0].cores

proc_env_ok = {
    proc.ENV_PROC_FS: helpers.procfs_dir("ok"),
    topology.ENV_LSCPU_SYSFS: helpers.sysfs_dir("xeon_d")
}


def test_kcm_init():
    args = ["init",
            "--conf-dir={}".format(os.path.join(tempfile.mkdtemp(), "init"))]

    helpers.execute(integration.kcm(), args, proc_env_ok)


def test_kcm_init_exists():
    args = ["init",
            "--conf-dir={}".format(helpers.conf_dir("minimal"))]

    with pytest.raises(subprocess.CalledProcessError):
        helpers.execute(integration.kcm(), args, proc_env_ok)


def test_kcm_init_wrong_assignment():
    args = ["init",
            "--num-dp-cores=1",
            "--num-cp-cores=1",
            "--conf-dir={}".format(helpers.conf_dir("ok"))]

    with pytest.raises(subprocess.CalledProcessError) as e:
        helpers.execute(integration.kcm(), args, proc_env_ok)

    assert "ERROR:root:4 dataplane cores (1 requested)" in str(e.value.output)


def test_kcm_init_insufficient_isolated_cores():
    proc_env_few_isolated = {
        proc.ENV_PROC_FS: helpers.procfs_dir("insufficient_isolated_cores"),
        topology.ENV_LSCPU_SYSFS: helpers.sysfs_dir("xeon_d")
    }

    args = ["init", "--conf-dir={}".format(
        os.path.join(tempfile.mkdtemp(), "init"))]

    with pytest.raises(subprocess.CalledProcessError) as e:
        helpers.execute(integration.kcm(), args, proc_env_few_isolated)

    assert (
        "ERROR:root:Cannot use isolated cores for "
        "data plane and control plane cores: not enough isolated") in \
        str(e.value.output)


def test_kcm_init_isolated_cores_mismatch():
    proc_env_isolated_mismatch = {
        proc.ENV_PROC_FS: helpers.procfs_dir("isolated_core_mismatch"),
        topology.ENV_LSCPU_SYSFS: helpers.sysfs_dir("xeon_d")
    }

    args = ["init",
            "--num-dp-cores=1",
            "--num-cp-cores=1",
            "--conf-dir={}".format(os.path.join(tempfile.mkdtemp(), "init"))]

    output = helpers.execute(
        integration.kcm(), args, proc_env_isolated_mismatch)

    assert ("WARNING:root:Not all isolated cores will be used "
            "by data and control plane") in str(output)


def test_kcm_init_partial_isolation():
    proc_env_partially_isolated = {
        proc.ENV_PROC_FS: helpers.procfs_dir("partially_isolated_cores"),
        topology.ENV_LSCPU_SYSFS: helpers.sysfs_dir("xeon_d")
    }

    args = ["init",
            "--num-dp-cores=1",
            "--num-cp-cores=1",
            "--conf-dir={}".format(os.path.join(tempfile.mkdtemp(), "init"))]

    output = helpers.execute(
        integration.kcm(), args, proc_env_partially_isolated)

    assert "WARNING:root:Physical core 1 is partially isolated" in str(output)
    assert "WARNING:root:Physical core 2 is partially isolated" in str(output)


def test_kcm_init_insufficient_cores():
    args = ["init",
            "--num-dp-cores=10",
            "--num-cp-cores=5",
            "--conf-dir={}".format(os.path.join(tempfile.mkdtemp(), "init"))]

    with pytest.raises(subprocess.CalledProcessError) as e:
        helpers.execute(integration.kcm(), args, proc_env_ok)

    assert ("ERROR:root:10 cores requested for dataplane. "
            "Only 8 cores available") in str(e.value.output)


def test_kcm_init_isolcpus():
    proc_env_partially_isolated = {
        proc.ENV_PROC_FS: helpers.procfs_dir("correctly_isolated_cores"),
        topology.ENV_LSCPU_SYSFS: helpers.sysfs_dir("xeon_d")
    }

    args = ["init",
            "--conf-dir={}".format(os.path.join(tempfile.mkdtemp(), "init"))]

    output = helpers.execute(
        integration.kcm(), args, proc_env_partially_isolated)

    print("captured output: '%s'", str(output))

    assert "INFO:root:Isolated logical cores: 0,1,2,3,4,8,9,10,11,12" \
           in str(output)

    assert "INFO:root:Isolated physical cores: 0,1,2,3,4" in str(output)

    assert "INFO:root:Adding cpu list 0,8 to dataplane pool." in str(output)
    assert "INFO:root:Adding cpu list 1,9 to dataplane pool." in str(output)
    assert "INFO:root:Adding cpu list 2,10 to dataplane pool." in str(output)
    assert "INFO:root:Adding cpu list 3,11 to dataplane pool." in str(output)

    assert "INFO:root:Adding cpu list 4,12 to controlplane pool." \
           in str(output)

    assert "INFO:root:Adding cpu list 5,13,6,14,7,15 to infra pool." \
           in str(output)
