#!/usr/bin/env python3
"""Create a secret-safe effective-runtime snapshot from named environment values."""
import argparse, hashlib, hmac, json, os
from pathlib import Path

def main():
    parser=argparse.ArgumentParser(); parser.add_argument("--spec", required=True); parser.add_argument("--output", required=True); args=parser.parse_args()
    key=os.environ.get("ISOLATION_FINGERPRINT_KEY", "").encode()
    if len(key) < 32: raise SystemExit("ISOLATION_FINGERPRINT_KEY must contain at least 32 bytes")
    spec=json.loads(Path(args.spec).read_text()); effective={}
    for category, names in spec["environment_variables"].items():
        values=[]
        for name in names:
            if name not in os.environ: raise SystemExit(f"required runtime variable is missing: {name}")
            values.append("sha256:"+hmac.new(key, os.environ[name].encode(), hashlib.sha256).hexdigest())
        effective[category]=values if len(values)>1 else values[0]
    output={"database_identity":spec["database_identity"],"redis_identity":spec["redis_identity"],"production_fingerprints":spec["production_fingerprints"],"effective":effective}
    Path(args.output).write_text(json.dumps(output,indent=2,sort_keys=True)+"\n")
    print(f"wrote secret-safe runtime evidence to {args.output}")
if __name__ == "__main__": main()
