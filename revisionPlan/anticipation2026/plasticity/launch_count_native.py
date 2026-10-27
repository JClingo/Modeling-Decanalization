import pathlib,time,unreal
started=time.monotonic()
script_path=pathlib.Path(unreal.Paths.project_dir()).resolve().parents[1]/'count_rule_native.py'
def count_audit_tick(dt):
 if time.monotonic()-started<2:return
 unreal.unregister_slate_post_tick_callback(count_audit_handle)
 exec(compile(script_path.read_text(),str(script_path),'exec'),globals())
count_audit_handle=unreal.register_slate_post_tick_callback(count_audit_tick)
