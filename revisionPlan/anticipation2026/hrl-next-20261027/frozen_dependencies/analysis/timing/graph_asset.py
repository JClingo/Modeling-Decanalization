"""UE 5.5 uncooked graph pin audit, using native serialization layout from engine source.

Preserves opaque bytes and records field offsets for tightly scoped edits.
"""
import base64
import json
import struct
from pathlib import Path

class Reader:
    def __init__(self, data, names):
        self.data, self.names, self.pos = data, names, 0
    def take(self, n):
        assert 0 <= n <= len(self.data) - self.pos, (self.pos, n, len(self.data))
        b = self.data[self.pos:self.pos+n]
        self.pos += n
        return b
    def i32(self): return struct.unpack('<i', self.take(4))[0]
    def u8(self): return self.take(1)[0]
    def name(self):
        i, suffix = self.i32(), self.i32()
        return self.names[i] + (f'_{suffix-1}' if suffix else '')
    def string(self):
        n = self.i32()
        b = self.take(abs(n) * (2 if n < 0 else 1))
        return b.decode('utf-16-le' if n < 0 else 'utf-8').rstrip('\0')
    def text(self):
        self.i32()  # flags
        history = self.u8()
        if history == 255:
            return self.string() if self.i32() else ''
        if history == 0:
            return [self.string(), self.string(), self.string()]
        if history == 1:
            pattern = self.text()
            values = {}
            for _ in range(self.i32()):
                key, kind = self.string(), self.u8()
                values[key] = self.text() if kind == 4 else self.take(4 if kind == 2 else 8).hex()
            return [pattern, values]
        raise ValueError(('FText history', history, self.pos))
    def ref(self):
        return None if self.i32() else (self.i32(), self.take(16).hex())
    def refs(self): return [self.ref() for _ in range(self.i32())]

def pins(asset, export):
    r = Reader(base64.b64decode(export['Extras']), asset['NameMap'])
    count = r.i32()
    assert 0 <= count < 300, count
    result = []
    for _ in range(count):
        start = r.pos
        ref = r.ref()
        assert ref is not None
        owner, guid = r.i32(), r.take(16).hex()
        assert (owner, guid) == ref
        name = r.name()
        friendly = r.text()
        source_index = r.i32()
        tooltip = r.string()
        direction = r.u8()
        category, subcategory, obj = r.name(), r.name(), r.i32()
        container = r.u8()
        if container == 3:
            r.name(); r.name(); r.i32(); r.i32(); r.i32(); r.i32()
        r.i32(); r.i32()  # ref, weak
        r.i32(); r.name(); r.take(16)  # member reference
        r.i32(); r.i32(); r.i32()  # const, wrapper, single precision
        default_start = r.pos
        default = r.string()
        default_end = r.pos
        auto_default = r.string()
        r.i32(); r.text()
        links_start = r.pos
        links = r.refs()
        links_end = r.pos
        subpins = r.refs()
        r.ref(); r.ref(); r.take(16); flags = r.i32()
        result.append(dict(name=name, guid=guid, owner=owner, direction=direction,
                           category=category, subcategory=subcategory, default=default,
                           auto_default=auto_default, links=links, subpins=subpins,
                           start=start, end=r.pos, default_start=default_start,
                           default_end=default_end, links_start=links_start, links_end=links_end))
    # Subclasses append native state (e.g. event/function flags or cast purity).
    assert r.pos <= len(r.data), (export['ObjectName'], r.pos, len(r.data))
    return result

def load(name): return json.loads(Path('Saved/TimingFix', name+'.json').read_text(encoding='utf-8'))

def audit(name):
    a = load(name)
    nodes, errors = {}, []
    for i, e in enumerate(a['Exports'], 1):
        if e['ObjectName'].startswith('K2Node_'):
            try:
                nodes[i] = dict(name=e['ObjectName'], outer=e['OuterIndex'], pins=pins(a,e),
                                properties={p['Name']: p.get('Value') for p in e.get('Data',[])})
            except Exception as exc:
                errors.append((i, e['ObjectName'], str(exc)))
    Path('Saved/TimingFix', name+'.graph.json').write_text(json.dumps(dict(nodes=nodes, errors=errors), indent=2), encoding='utf-8')
    print(name, len(nodes), 'nodes;', len(errors), 'parse errors', errors[:5])
    return nodes

if __name__ == '__main__':
    for name in ['BP_Agent', 'BP_GameMode', 'BP_AgentManager', 'BP_AgentInteractor', 'BP_AgentTrainingEnv']:
        audit(name)
