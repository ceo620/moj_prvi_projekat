#!/usr/bin/env python3
import os,sys,json,hashlib,ast,subprocess,signal
from pathlib import Path

BATCH="IPHONE_888_ENGINE_CALLSITE_TRACE_14"
ROOT=Path("/root/FREYA_IPHONE_ISH_NODE_888")
ENGINE=ROOT/"05_SYSTEM_RUNTIME/ENGINE__01cd6ee9c07d.py"
TEST=ROOT/"10_RUNTIME_TEST"
OUT=ROOT/(BATCH+".json")
EXPECTED="01cd6ee9c07d76f2b974b655791c4bcb8426e128bdb29ca221cfcce502064525"

print("PROTOCOL=888",flush=True); print("BATCH="+BATCH,flush=True)
print("HUMAN_GATE=ACTIVE",flush=True); print("FAIL_CLOSED=YES",flush=True)
def hold(x): print("HOLD="+x,flush=True); raise SystemExit(2)
signal.signal(signal.SIGALRM,lambda *_:hold("TIMEOUT")); signal.alarm(120)

u=os.uname()
if os.geteuid()!=0 or u.sysname!="Linux" or u.machine!="i686" or "ish" not in u.release.lower():
    hold("IPHONE_IDENTITY_NOT_PROVEN")
raw=ENGINE.read_bytes() if ENGINE.is_file() else b""
if hashlib.sha256(raw).hexdigest()!=EXPECTED: hold("ENGINE_MISSING_OR_HASH_CHANGED")
src=raw.decode("utf-8")
tree=ast.parse(src)

TARGETS={"open","read_text","read_bytes","write_text","write_bytes","mkdir","replace",
         "rename","unlink","remove","copy","copyfile","move","stat","exists","is_file","is_dir"}

class TraceCalls(ast.NodeTransformer):
    def visit_Call(self,node):
        self.generic_visit(node)
        name=""
        if isinstance(node.func,ast.Name): name=node.func.id
        elif isinstance(node.func,ast.Attribute): name=node.func.attr
        if name not in TARGETS: return node
        # Avoid wrapping our injected helper.
        if isinstance(node.func,ast.Name) and node.func.id=="__trace_call_888": return node
        label=f"{name}@L{getattr(node,'lineno',0)}"
        return ast.copy_location(
            ast.Call(func=ast.Name(id="__trace_call_888",ctx=ast.Load()),
                     args=[ast.Constant(label),node.func,*node.args],
                     keywords=node.keywords),node)

tree=TraceCalls().visit(tree); ast.fix_missing_locations(tree)
helper=ast.parse(