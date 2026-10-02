import os, stat, subprocess

if os.geteuid() != 0 or 'ish' not in os.uname().release.lower():
    raise SystemExit('HOLD=OVO_SE_POKRECE_U_IPHONE_ISH')
d = '/root/IPHONE_ASUS_KLJUC_888'
k = d + '/id_ed25519'
print('BATCH=IPHONE_MOZAK_004; NETWORK_CALLS=0', flush=True)
try:
    if not os.path.lexists(d):
        os.mkdir(d, 0o700)
    s = os.lstat(d)
    if not stat.S_ISDIR(s.st_mode) or s.st_uid != 0 or stat.S_IMODE(s.st_mode) != 0o700:
        raise ValueError('KEY_DIRECTORY_TYPE_OWNER_OR_PERMISSIONS')
    existing = any(os.path.lexists(p) for p in (k, k + '.pub'))
    if not existing:
        subprocess.run(
            ['ssh-keygen', '-q', '-t', 'ed25519', '-N', '',
             '-C', 'IPHONE_ASUS_888', '-f', k],
            stdin=subprocess.DEVNULL, check=True, timeout=20)
    for p in (k, k + '.pub'):
        s = os.lstat(p)
        if not stat.S_ISREG(s.st_mode) or s.st_uid != 0 or not 0 < s.st_size < 4096:
            raise ValueError('KEY_FILE_TYPE_OWNER_OR_SIZE')
        if p == k and stat.S_IMODE(s.st_mode) & 0o077:
            raise ValueError('PRIVATE_KEY_PERMISSIONS')
    public = subprocess.run(
        ['ssh-keygen', '-y', '-P', '', '-f', k],
        stdin=subprocess.DEVNULL, stdout=subprocess.PIPE,
        check=True, timeout=10).stdout.decode('ascii').split()
    with open(k + '.pub', 'r', encoding='ascii') as f:
        saved = f.read(4096).split()
    if len(public) < 2 or public[0] != 'ssh-ed25519' or saved[:2] != public[:2]:
        raise ValueError('PUBLIC_PRIVATE_PAIR_MISMATCH')
    print('ACTION=' + ('EXISTING_PAIR_VERIFIED' if existing else 'NEW_PAIR_CREATED'))
    print('PRIVATE_KEY_PATH=' + k)
    print('PUBLIC_KEY=' + ' '.join(public[:2]) + ' IPHONE_ASUS_888')
    print('PAIR_CHECK=PASS; EXISTING_FILES_OVERWRITTEN=0')
    print('ASUS_ACCESS=NOT_CONFIGURED; PACKET_SENT=NO')
except (OSError, ValueError, subprocess.SubprocessError) as e:
    print('HOLD=' + type(e).__name__ + ': ' + str(e)[:180])
print('NEXT=VRATI_IZLAZ_SA_JAVNIM_KLJUCEM')
