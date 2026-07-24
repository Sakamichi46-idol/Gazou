# GAZOU_UPLOAD 低通信量版

## 変更点

- Discordへの通常表示は、画像ファイルの再アップロードではなく元画像URLを使います。
- 1回のメッセージにつき最大10枚をEmbedでまとめて表示します。
- URL表示に失敗した場合、アーカイブ送信処理は従来の添付方式へ自動で切り替わります。
- 写真検索ではローカル保存画像を毎回Discordへ再送しません。
- AI解析では長辺1024px・JPEG品質78を既定値として縮小画像を送ります。
- 保存済み画像と既存SQLite DBは削除・初期化しません。

## Railway Variables

```text
LOW_EGRESS_MODE=true
IMAGE_EMBEDS_PER_MESSAGE=10
PHOTO_AI_MAX_DIMENSION=1024
PHOTO_AI_JPEG_QUALITY=78
```

`LOW_EGRESS_MODE=false` にすると従来の画像添付方式へ戻せます。

## 表示上の違い

画像はこれまでと同じくDiscord内に表示されます。ただし、添付画像のグリッドではなく、最大10個の画像Embedとして表示されるため、端末によっては縦並びになります。

## 大切な点

この版は既存の保存画像を維持します。新着画像も従来の写真アーカイブ処理で保存されます。節約するのは主に「同じ画像をDiscordへ何度もアップロードする通信」です。
