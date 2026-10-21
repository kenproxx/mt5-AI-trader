"""Exercise the PowerShell boundary without a Python executable or MT5."""
import os
import shutil
import subprocess
from pathlib import Path

import pytest

POWERSHELL = shutil.which('powershell') or shutil.which('pwsh')
pytestmark = pytest.mark.skipif(POWERSHELL is None, reason='PowerShell is required')


@pytest.mark.parametrize(('flag', 'expected_error'), [
    ('-ExecuteDemo', 'NamedParameterNotFound'),
    ('-Execute', 'Missing .venv'),
])
def test_launcher_binds_execution_flag_before_running_body(tmp_path, flag, expected_error):
    scripts = tmp_path / 'scripts'
    scripts.mkdir()
    launcher = scripts / 'run_vps_basket.ps1'
    source = Path(__file__).resolve().parents[1] / 'scripts' / launcher.name
    shutil.copyfile(source, launcher)
    # No .venv in this isolated project: valid arguments reach that check;
    # retired arguments must fail in parameter binding before entering the body.
    env = dict(os.environ, MT5_TEST_LAUNCHER=str(launcher))
    result = subprocess.run([
        POWERSHELL, '-NoProfile', '-NonInteractive', '-ExecutionPolicy', 'Bypass',
        '-Command', 'try { & $env:MT5_TEST_LAUNCHER -AccountLogin 123 ' + flag +
        '; exit 0 } catch { [Console]::Error.WriteLine($_.FullyQualifiedErrorId); exit 1 }',
    ], env=env, text=True, capture_output=True, timeout=30, check=False)
    assert result.returncode == 1, result.stdout + result.stderr
    assert expected_error in result.stderr, result.stderr
