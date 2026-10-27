using UAssetAPI;
using UAssetAPI.UnrealTypes;
using UAssetAPI.ExportTypes;
try {
    if (args[0] == "export") {
        var asset = new UAsset(args[1], EngineVersion.VER_UE5_5);
        File.WriteAllText(args[2], asset.SerializeJson());
        Console.WriteLine("Exported " + args[1] + "; binary equality: " + asset.VerifyBinaryEquality());
    } else if (args[0] == "import") {
        var asset = UAsset.DeserializeJson(File.ReadAllText(args[1]));
        var originalSizes = asset.Exports.Select(e => (e.SerialSize, e is NormalExport n ? n.Extras.Length : 0, e.ScriptSerializationEndOffset)).ToArray();
        // UAssetAPI recalculates export sizes, but keeps UE5 script property end
        // offsets. Preserve their original position relative to native extras.
        asset.Write(args[2]);
        for (int i = 0; i < asset.Exports.Count; i++) {
            var e = asset.Exports[i];
            var old = originalSizes[i];
            if (old.ScriptSerializationEndOffset > 0 && e.GetType() == typeof(NormalExport)) {
                var n = (NormalExport)e;
                e.ScriptSerializationEndOffset = e.SerialSize - n.Extras.Length - (e.ObjectFlags.HasFlag(EObjectFlags.RF_ClassDefaultObject) ? 0 : 4);
            }
        }
        asset.Write(args[2]);
        Console.WriteLine("Wrote " + args[2]);
    }
} catch (Exception ex) { Console.Error.WriteLine(ex); Environment.Exit(1); }
