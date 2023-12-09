# otlp receiver

## setup

```bash
# run the fastapi receiver and the otel pipeline
docker-compose up -d --force-recreate --build

# start log triggering app (and visit endpoint)
source venv/bin/activate
pip install
python app.py
```

## nix env fix

```nix
{ pkgs ? import <nixpkgs> {}, stdenv ? pkgs.stdenv }:

pkgs.mkShell {
  buildInputs = [
    pkgs.python311
    pkgs.poetry
  ];

  shellHook = ''
    # fixes libstdc++ issues and libgl.so issues
    export LD_LIBRARY_PATH=${stdenv.cc.cc.lib}/lib:$LD_LIBRARY_PATH
  '';
}
```
