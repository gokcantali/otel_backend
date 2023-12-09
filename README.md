# otel backend

This setup is a POC of an otel backend that can receive otlp
logs, metrics and traces. The backend is a fastapi app parsing and
logging the received payload.
The `otel_generator.py` on the other hand is a flask app that sends
some dummy logs, metrics and traces to the collector.

```text
otel_generator --> otel collector (docker) --> otel backend (docker)
```

## setup

```bash
# run the fastapi receiver and the otel pipeline
docker-compose up -d --force-recreate --build
docker-compose logs -f otel_backend

# generate traces, logs, metrics
poetry install
poetry run python otel_generator.py
curl http://127.0.0.1:5000
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
