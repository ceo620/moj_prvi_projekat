#!/usr/bin/env python3
"""Protocol 888: one explicitly approved iPhone -> ASUS package reception.

No extraction, document processing, overwriting, remote deletion or retries.
Original source files remain unchanged. A receipt is created on ASUS only.
The only temporary local write is a pinned known_hosts file, removed on exit.
Requires existing Python 3, OpenSSH client and the already configured key.
Windows receiver requires PowerShell 5.1 and read access to reparse metadata.
Cloud reparse tags are checked; redirects and nonresident paths fail closed.
No installer, elevation, policy bypass, service or scheduled task is used.

Review references:
https://learn.microsoft.com/en-us/windows-server/administration/windows-commands/fsutil-reparsepoint
https://learn.microsoft.com/en-us/windows/win32/fileio/file-attribute-constants
https://man.openbsd.org/ssh_config
"""

import base64
import hashlib
import json
import os
import shutil
import stat
import subprocess
import sys
import tempfile

BATCH = "IPHONE_ASUS_024_PRENOS_888"
SOURCE = "/root/mozak uzivo iphone/ZA_SLANJE/PAKET_cc5b080b7027_07dc7d558863"
ZIP_NAME = "IPHONE_ZA_ASUS_888.zip"
MANIFEST_NAME = "SPREMNO_ZA_PREGLED.json"
ZIP_BYTES = 476332
ZIP_SHA = "09372246860fb8ad08a063b1ecba5d181dc80cbc656b501b4945ad16a6f8a59f"
SNAPSHOT = "cc5b080b7027e198ce5a59bf4ba18acf0e96f98a0da51fd458e92f4bf1235d85"
KEY = "/root/IPHONE_ASUS_KLJUC_888/id_ed25519"
USER_KEY = "AAAAC3NzaC1lZDI1NTE5AAAAIElMnjrWfg9FavFvAyK4EQn/ahifKWQrC8d4cBgQHALE"
HOST_KEY = "AAAAC3NzaC1lZDI1NTE5AAAAIGxDgw5DmY80kHLhpDuL8GVhSy8VAO9MCc/U5ojV5Z1m"
DEST = r"C:\Users\ceo\OneDrive\Desktop\mozak uzivo iphone\PAKET_cc5b080b7027_07dc7d558863"


class Hold(Exception):
    pass


def require(condition, reason):
    if not condition:
        raise Hold(reason)


def emit(event, **fields):
    print(json.dumps(dict(batch=BATCH, event=event, **fields), ensure_ascii=True), flush=True)


def sha(data):
    return hashlib.sha256(data).hexdigest()


def ancestors(path):
    require(path.startswith("/") and "/../" not in path, "SOURCE_SCOPE")
    current = "/"
    for part in path.split("/")[1:-1]:
        current = os.path.join(current, part)
        info = os.lstat(current)
        require(stat.S_ISDIR(info.st_mode) and not stat.S_ISLNK(info.st_mode),
                "SOURCE_DIRECTORY_REDIRECT:" + current)


def regular_info(path, exact=None, limit=16384, private=False):
    ancestors(path)
    info = os.lstat(path)
    require(stat.S_ISREG(info.st_mode) and info.st_nlink == 1, "FILE_TYPE_OR_LINKS:" + path)
    require(0 < info.st_size <= limit, "FILE_BUDGET:" + path)
    require(exact is None or info.st_size == exact, "FILE_SIZE:" + path)
    if private:
        require(info.st_uid == os.geteuid() and info.st_mode & 0o077 == 0,
                "PRIVATE_KEY_OWNER_OR_PERMISSIONS")
    return info


def read_exact(path, size):
    before = regular_info(path, exact=size, limit=size)
    fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
    with os.fdopen(fd, "rb") as stream:
        current = os.fstat(stream.fileno())
        require(stat.S_ISREG(current.st_mode) and current.st_nlink == 1 and
                (current.st_dev, current.st_ino, current.st_size) ==
                (before.st_dev, before.st_ino, size), "FILE_CHANGED_BEFORE_READ")
        data = stream.read(size + 1)
        after = os.fstat(stream.fileno())
    require(len(data) == size and
            (after.st_size, after.st_mtime_ns, after.st_ctime_ns) ==
            (current.st_size, current.st_mtime_ns, current.st_ctime_ns),
            "FILE_CHANGED_DURING_READ")
    return data


def unique_object(pairs):
    result = {}
    for name, value in pairs:
        require(name not in result, "DUPLICATE_JSON_FIELD:" + name)
        result[name] = value
    return result


def validate_manifest(data):
    value = json.loads(data.decode("utf-8"), object_pairs_hook=unique_object)
    expected = {
        "asus_receipt": None,
        "background_service_started": False,
        "batch": "IPHONE_MOZAK_001_PRIPREMA_888",
        "network_calls": 0,
        "observed_utc": "2026-09-20T22:37:44.714778+00:00",
        "packet": SOURCE + "/" + ZIP_NAME,
        "packet_bytes": ZIP_BYTES,
        "packet_sha256": ZIP_SHA,
        "readback": "PASS",
        "result": "LOCAL_REVIEW_PACKET_READY_NOT_SENT",
        "saved_findings": 43,
        "snapshot_id": SNAPSHOT,
        "source_count": 11,
    }
    require(isinstance(value, dict) and value.keys() == expected.keys(), "MANIFEST_SCHEMA")
    for name, wanted in expected.items():
        require(type(value[name]) is type(wanted) and value[name] == wanted,
                "MANIFEST_CONTRACT:" + name)


RECEIVER = r'''
$ErrorActionPreference = 'Stop'
Set-StrictMode -Version 2.0
$created = New-Object 'System.Collections.Generic.List[string]'
$streams = New-Object 'System.Collections.Generic.List[System.IDisposable]'
$newDirectory = $false
$batch = 'IPHONE_ASUS_024_PRENOS_888'
$root = 'C:\Users\ceo\OneDrive\Desktop\mozak uzivo iphone'
$dest = $root + '\PAKET_cc5b080b7027_07dc7d558863'
$zipSha = '09372246860fb8ad08a063b1ecba5d181dc80cbc656b501b4945ad16a6f8a59f'
$manifestSha = $null
$zipPath = $dest + '\IPHONE_ZA_ASUS_888.zip'
$manifestPath = $dest + '\SPREMNO_ZA_PREGLED.json'
$receiptPath = $dest + '\PRIJEM_ASUS_888.json'

function Emit([System.Collections.IDictionary]$value) {
    [Console]::Out.WriteLine(($value | ConvertTo-Json -Compress -Depth 6))
}
function Digest([byte[]]$bytes) {
    $h = [Security.Cryptography.SHA256]::Create()
    try { return ([BitConverter]::ToString($h.ComputeHash($bytes))).Replace('-','').ToLowerInvariant() }
    finally { $h.Dispose() }
}
function Check-Directory([string]$path) {
    $item = Get-Item -LiteralPath $path -Force -ErrorAction Stop
    if (!($item -is [IO.DirectoryInfo])) { throw "HOLD_DIRECTORY_TYPE:$path" }
    $attrs = [long]$item.Attributes
    if (($attrs -band 0x441000) -ne 0) { throw "HOLD_NONRESIDENT_DIRECTORY:$path" }
    if (($attrs -band 0x400) -ne 0) {
        if ($path -cne 'C:\Users\ceo\OneDrive' -and
            !$path.StartsWith('C:\Users\ceo\OneDrive\', [StringComparison]::Ordinal)) {
            throw "HOLD_REPARSE_OUTSIDE_ONEDRIVE:$path"
        }
        $query = @(& 'C:\Windows\System32\fsutil.exe' reparsepoint query $path 2>&1)
        if ($LASTEXITCODE -ne 0) { throw "HOLD_REPARSE_QUERY_DENIED_OR_FAILED:$path" }
        $match = [regex]::Match(($query -join "`n"), '0x[0-9a-fA-F]{8}')
        if (!$match.Success -or $match.Value -notmatch '^0x9000[0-9a-fA-F]01[aA]$') {
            throw "HOLD_UNKNOWN_OR_REDIRECTING_REPARSE:$path"
        }
        Emit ([ordered]@{event='CLOUD_DIRECTORY_METADATA';path=$path;tag=$match.Value})
    }
}
function Check-Ancestors {
    foreach ($path in @('C:\','C:\Users','C:\Users\ceo','C:\Users\ceo\OneDrive',
                       'C:\Users\ceo\OneDrive\Desktop',$root)) {
        Check-Directory $path
    }
}
function Write-NewVerified([string]$path, [byte[]]$bytes, [string]$expectedSha) {
    if ($path -cne $zipPath -and $path -cne $manifestPath -and $path -cne $receiptPath) {
        throw 'HOLD_WRITE_SCOPE'
    }
    Check-Ancestors
    Check-Directory $dest
    $stream = [IO.File]::Open($path, [IO.FileMode]::CreateNew,
                            [IO.FileAccess]::ReadWrite, [IO.FileShare]::None)
    $streams.Add($stream)
    $created.Add($path)
    $stream.Write($bytes, 0, $bytes.Length)
    $stream.Flush($true)
    if ($stream.Length -ne $bytes.Length) { throw "HOLD_READBACK_SIZE:$path" }
    $stream.Position = 0
    $hash = [Security.Cryptography.SHA256]::Create()
    try { $observed = ([BitConverter]::ToString($hash.ComputeHash($stream))).Replace('-','').ToLowerInvariant() }
    finally { $hash.Dispose() }
    if ($observed -cne $expectedSha) { throw "HOLD_READBACK_HASH:$path" }
    Emit ([ordered]@{event='FILE_READBACK_PASS';path=$path;bytes=$bytes.Length;sha256=$observed})
}

try {
    if ($env:COMPUTERNAME -ine 'DANIJELA' -or $env:USERNAME -ine 'ceo' -or
        [Security.Principal.WindowsIdentity]::GetCurrent().Name -ine 'DANIJELA\ceo') {
        throw 'HOLD_WRONG_ASUS_CONTEXT'
    }
    if ($PSVersionTable.PSVersion.Major -lt 5) { throw 'HOLD_POWERSHELL_VERSION' }
    Emit ([ordered]@{event='ASUS_IDENTITY_PASS';host=$env:COMPUTERNAME;user=$env:USERNAME})
    $text = New-Object Text.StringBuilder
    $chunk = New-Object char[] 8192
    while (($n = [Console]::In.Read($chunk,0,$chunk.Length)) -gt 0) {
        if ($text.Length + $n -gt 650000) { throw 'HOLD_PAYLOAD_BUDGET' }
        [void]$text.Append($chunk,0,$n)
    }
    $payload = $text.ToString() | ConvertFrom-Json
    if (@($payload.PSObject.Properties.Name).Count -ne 4 -or
        $payload.protocol -cne '888' -or
        $payload.manifest_sha256 -cnotmatch '^[0-9a-f]{64}$' -or
        !($payload.zip_b64 -is [string]) -or !($payload.manifest_b64 -is [string])) {
        throw 'HOLD_PAYLOAD_SCHEMA'
    }
    $zip = [Convert]::FromBase64String($payload.zip_b64)
    $manifest = [Convert]::FromBase64String($payload.manifest_b64)
    $manifestSha = [string]$payload.manifest_sha256
    if ($zip.Length -ne 476332 -or (Digest $zip) -cne $zipSha -or
        $manifest.Length -ne 607 -or (Digest $manifest) -cne $manifestSha) {
        throw 'HOLD_PAYLOAD_SIZE_OR_HASH'
    }
    $utf8 = New-Object Text.UTF8Encoding($false, $true)
    $m = $utf8.GetString($manifest) | ConvertFrom-Json
    if ($m.packet_sha256 -cne $zipSha -or $m.packet_bytes -ne 476332 -or
        $m.snapshot_id -cne 'cc5b080b7027e198ce5a59bf4ba18acf0e96f98a0da51fd458e92f4bf1235d85' -or
        $m.result -cne 'LOCAL_REVIEW_PACKET_READY_NOT_SENT' -or $null -ne $m.asus_receipt) {
        throw 'HOLD_MANIFEST_RELATION'
    }
    Check-Ancestors
    if (Test-Path -LiteralPath $dest -ErrorAction Stop) { throw 'HOLD_DESTINATION_ALREADY_EXISTS_NO_REPLAY' }
    Emit ([ordered]@{event='PREFLIGHT_PASS';destination=$dest;files_to_create=3;overwrite=$false;extract=$false})
    $null = New-Item -ItemType Directory -Path $dest -ErrorAction Stop
    $newDirectory = $true
    Check-Directory $dest
    Write-NewVerified $zipPath $zip $zipSha
    Write-NewVerified $manifestPath $manifest $manifestSha
    $receipt = [ordered]@{
        protocol='888';batch=$batch;observed_utc=[DateTime]::UtcNow.ToString('o')
        human_gate_authority='Danijela Đurović Keskin'
        human_gate_scope='ONE_IPHONE_PACKAGE_MANIFEST_AND_RECEIPT_NO_EXTRACT_NO_OVERWRITE'
        status='RECEIVED_HASH_VERIFIED_NOT_OPENED';windows_host='DANIJELA';windows_user='ceo'
        package_path=$zipPath;package_bytes=476332;package_sha256=$zipSha
        manifest_path=$manifestPath;manifest_bytes=607;manifest_sha256=$manifestSha
        receipt_path=$receiptPath
        source_snapshot_id='cc5b080b7027e198ce5a59bf4ba18acf0e96f98a0da51fd458e92f4bf1235d85'
        verification='SHA256_READBACK_SAME_LOCKED_FILE_HANDLES'
        source_files_changed=$false;original_manifest_changed=$false
        overwritten_files=0;archives_opened=0;integration_executed=$false
        document_production_started=$false;other_nodes_contacted=$false
        receipt_copied_to_iphone=$false
    }
    $receiptBytes = $utf8.GetBytes(($receipt | ConvertTo-Json -Depth 6) + "`r`n")
    if ($receiptBytes.Length -gt 8192) { throw 'HOLD_RECEIPT_BUDGET' }
    $receiptSha = Digest $receiptBytes
    Write-NewVerified $receiptPath $receiptBytes $receiptSha
    foreach ($stream in $streams) { $stream.Dispose() }
    $streams.Clear()
    Emit ([ordered]@{
        event='ASUS_RECEIPT';receipt=$receipt;receipt_sha256=$receiptSha
        receipt_bytes=$receiptBytes.Length
    })
    Emit ([ordered]@{
        event='PASS_RECEIVED_HASH_VERIFIED';batch=$batch;destination=$dest
        files_created=3;directories_created=1;overwritten_files=0;archives_opened=0
        package_sha256=$zipSha;manifest_sha256=$manifestSha;receipt_sha256=$receiptSha
        integration_executed=$false;next='VRATI_CEO_IZLAZ'
    })
    exit 0
} catch {
    Emit ([ordered]@{
        event='HOLD';reason=$_.Exception.Message;destination=$dest
        new_directory_created=$newDirectory;files_created=@($created.ToArray())
        partial_files_preserved=$true;automatic_retry=$false
        overwritten_files=0;archives_opened=0;integration_executed=$false
        next='STOP_VRATI_CEO_IZLAZ_NE_PONAVLJAJ'
    })
    exit 1
} finally {
    foreach ($stream in $streams) { $stream.Dispose() }
}
'''


def wire_data(package, manifest):
    receiver = RECEIVER.encode("utf-8")
    require(len(receiver) <= 32768, "RECEIVER_BUDGET")
    payload = json.dumps({
        "protocol": "888", "zip_b64": base64.b64encode(package).decode("ascii"),
        "manifest_b64": base64.b64encode(manifest).decode("ascii"),
        "manifest_sha256": sha(manifest),
    }, separators=(",", ":")).encode("ascii")
    require(len(payload) <= 650000, "PAYLOAD_BUDGET")
    bootstrap = r'''
$ErrorActionPreference='Stop'
try {
    [Console]::OutputEncoding=New-Object Text.UTF8Encoding($false)
    $line=[Console]::In.ReadLine()
    if ($null -eq $line -or $line.Length -gt 44000) { throw 'HOLD_RECEIVER_BUDGET' }
    $bytes=[Convert]::FromBase64String($line)
    $h=[Security.Cryptography.SHA256]::Create()
    try { $sum=([BitConverter]::ToString($h.ComputeHash($bytes))).Replace('-','').ToLowerInvariant() }
    finally { $h.Dispose() }
    if ($sum -cne '__SHA__') { throw 'HOLD_RECEIVER_HASH' }
    & ([ScriptBlock]::Create([Text.Encoding]::UTF8.GetString($bytes)))
} catch {
    [Console]::Out.WriteLine('HOLD_BOOTSTRAP=' + $_.Exception.Message)
    exit 1
}
'''.replace("__SHA__", sha(receiver))
    encoded = base64.b64encode(bootstrap.encode("utf-16le")).decode("ascii")
    command = "powershell.exe -NoLogo -NoProfile -NonInteractive -EncodedCommand " + encoded
    require(len(command) < 7500, "WINDOWS_COMMAND_BUDGET")
    return command, base64.b64encode(receiver) + b"\n" + payload


def ssh_arguments(executable, pinned_file, command):
    options = [
        "BatchMode=yes", "IdentitiesOnly=yes", "IdentityAgent=none",
        "StrictHostKeyChecking=yes", "UserKnownHostsFile=" + pinned_file,
        "GlobalKnownHostsFile=/dev/null", "HostKeyAlgorithms=ssh-ed25519",
        "UpdateHostKeys=no", "VerifyHostKeyDNS=no", "ForwardAgent=no",
        "ClearAllForwardings=yes", "PasswordAuthentication=no",
        "KbdInteractiveAuthentication=no", "PreferredAuthentications=publickey",
        "AddKeysToAgent=no", "ConnectTimeout=10", "ConnectionAttempts=1",
        "ServerAliveInterval=10", "ServerAliveCountMax=3", "LogLevel=ERROR",
    ]
    args = [executable, "-F", "/dev/null", "-T", "-p", "22", "-i", KEY]
    for option in options:
        args += ["-o", option]
    return args + ["ceo@192.168.1.109", command]


def main():
    require(os.geteuid() == 0 and os.uname().nodename == "localhost" and
            "ish" in os.uname().release.lower(), "WRONG_IPHONE_ISH_CONTEXT")
    emit("START", mode="APPROVED_ONE_PACKAGE_TRANSFER", destination=DEST,
         unzip=False, overwrite=False, other_nodes=False)
    package = read_exact(SOURCE + "/" + ZIP_NAME, ZIP_BYTES)
    require(sha(package) == ZIP_SHA, "PACKAGE_SHA256")
    manifest = read_exact(SOURCE + "/" + MANIFEST_NAME, 607)
    validate_manifest(manifest)
    regular_info(KEY, private=True)
    ssh = shutil.which("ssh")
    keygen = shutil.which("ssh-keygen")
    require(ssh is not None and keygen is not None, "EXISTING_OPENSSH_TOOLS_MISSING")
    check = subprocess.run([keygen, "-y", "-P", "", "-f", KEY],
                           stdin=subprocess.DEVNULL, stdout=subprocess.PIPE,
                           stderr=subprocess.PIPE, timeout=15, check=False)
    require(check.returncode == 0 and
            check.stdout.decode("ascii").split()[:2] == ["ssh-ed25519", USER_KEY],
            "CONFIGURED_IPHONE_KEY_MISMATCH_OR_PROTECTED")
    emit("LOCAL_PREFLIGHT_PASS", package_bytes=len(package), package_sha256=sha(package),
         manifest_bytes=len(manifest), manifest_sha256=sha(manifest), original_writes=0)
    command, wire = wire_data(package, manifest)
    with tempfile.TemporaryDirectory(prefix="iphone_asus_024_", dir="/tmp") as temporary:
        pinned = os.path.join(temporary, "known_hosts")
        with open(pinned, "x", encoding="ascii") as output:
            os.chmod(pinned, 0o600)
            output.write("192.168.1.109 ssh-ed25519 " + HOST_KEY + "\n")
        emit("SSH_START", endpoint="ceo@192.168.1.109:22", host_key="PINNED_ED25519",
             authentication="ONE_EXISTING_IPHONE_KEY", automatic_retry=False)
        try:
            result = subprocess.run(ssh_arguments(ssh, pinned, command), input=wire,
                                    stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                    timeout=180, check=False)
        except subprocess.TimeoutExpired as error:
            if error.stdout:
                print(error.stdout.decode("utf-8", "replace"), flush=True)
            raise Hold("SSH_TIMEOUT_REMOTE_STATE_UNKNOWN_DO_NOT_REPEAT") from None
    text = result.stdout.decode("utf-8", "replace")
    print(text, end="" if text.endswith("\n") else "\n", flush=True)
    if result.stderr:
        print("SSH_DIAGNOSTIC=" + json.dumps(result.stderr.decode("utf-8", "replace")), flush=True)
    require(result.returncode == 0, "SSH_OR_RECEIVER_FAILED_STATE_MAY_BE_PARTIAL_DO_NOT_REPEAT")
    records = []
    for line in text.splitlines():
        try:
            item = json.loads(line)
            if isinstance(item, dict):
                records.append(item)
        except ValueError:
            pass
    passed = [r for r in records if r.get("event") == "PASS_RECEIVED_HASH_VERIFIED"]
    require(len(passed) == 1 and passed[0].get("destination") == DEST and
            passed[0].get("package_sha256") == ZIP_SHA and
            passed[0].get("manifest_sha256") == sha(manifest) and
            passed[0].get("files_created") == 3, "REMOTE_RECEIPT_MISSING_OR_MISMATCH")
    emit("TRANSFER_CONFIRMED", receipt_location="ASUS_ONLY_AND_THIS_CONSOLE_OUTPUT",
         originals_changed=False, unpacked=False, integration_executed=False,
         temporary_host_key_file_removed=True, next="VRATI_CEO_IZLAZ")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        emit("HOLD", reason="INTERRUPTED_REMOTE_STATE_UNKNOWN_DO_NOT_REPEAT", next="VRATI_CEO_IZLAZ")
        sys.exit(1)
    except Exception as error:
        emit("HOLD", reason=str(error), error_type=type(error).__name__,
             automatic_retry=False, next="VRATI_CEO_IZLAZ_NE_PONAVLJAJ")
        sys.exit(1)
