import pathlib,time,unreal
started=time.monotonic()
script=pathlib.Path(unreal.Paths.project_dir()).resolve().parents[1]/'validate_native.py'
def tick(dt):
    if time.monotonic()-started<2:return
    unreal.unregister_slate_post_tick_callback(handle)
    exec(compile(script.read_text(),str(script),'exec'),globals())
handle=unreal.register_slate_post_tick_callback(tick)
