"""Install the verified Microsoft OpenMP DLL required by UE 5.5 PyTorch 2.4.0.
Run with Intermediate/PipInstall/Scripts/python.exe after recreating PipInstall.
"""
import hashlib
import io
import json
import pathlib
import urllib.request
import zipfile

ROOT = pathlib.Path(__file__).resolve().parents[2]
PACKAGE_SHA = '8b1db85a80ed5ff9c031de38176bf5f108e3f796919c817eb0106445a8a218a6'
DLL_SHA = 'fbf06c5dba408b4e27d22d00d2fd8a4ba09b0a7747d5e8c006b80cef3079f47e'
URL = ('https://download.visualstudio.microsoft.com/download/pr/'
       '8e1ea566-8bfc-4707-b05e-bee74606db7d/' + PACKAGE_SHA +
       '/Microsoft.VC.14.40.17.10.CRT.Redist.X64.base.vsix')
MEMBER = ('Contents/VC/Redist/MSVC/14.40.33807/debug_nonredist/'
          'x64/Microsoft.VC143.OpenMP.LLVM/libomp140.x86_64.dll')

def main():
    target = ROOT / 'Intermediate/PipInstall/Lib/site-packages/torch/lib/libomp140.x86_64.dll'
    if not target.parent.is_dir():
        raise RuntimeError('Project PyTorch installation is missing')
    data = urllib.request.urlopen(URL, timeout=60).read()
    if hashlib.sha256(data).hexdigest() != PACKAGE_SHA:
        raise RuntimeError('Microsoft package checksum mismatch')
    with zipfile.ZipFile(io.BytesIO(data)) as package:
        dll = package.read(MEMBER)
    if hashlib.sha256(dll).hexdigest() != DLL_SHA:
        raise RuntimeError('OpenMP DLL checksum mismatch')
    if target.exists() and hashlib.sha256(target.read_bytes()).hexdigest() != DLL_SHA:
        raise RuntimeError('Refusing to overwrite a different existing runtime')
    if not target.exists():
        target.write_bytes(dll)
    saved = ROOT / 'Saved/PythonRuntimeFix'
    saved.mkdir(parents=True, exist_ok=True)
    metadata = {'source': URL, 'package_sha256': PACKAGE_SHA, 'member': MEMBER,
                'dll_sha256': DLL_SHA, 'installed_to': str(target)}
    (saved / 'runtime_source.json').write_text(json.dumps(metadata, indent=2))
    print(json.dumps(metadata, indent=2))

if __name__ == '__main__':
    main()
