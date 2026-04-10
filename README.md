# put-key

Linux カーネルキーリング（`@u` / ユーザーキーリング）にシークレットを登録するシンプルな GTK4 GUI ツールです。
パスワードマネージャーなどで管理しているシークレットを、コマンドラインの履歴に残さずキーリングへ登録するために使います。

## 使い方

```bash
python3 put-key.py <keyname>
```

例：

```bash
python3 put-key.py my_api_key
```

ウィンドウが開くので、シークレット値を入力して OK を押すと `@u`（ユーザーキーリング）に登録されます。

### 多重起動防止

同じキー名で既にウィンドウが開いている場合、2つ目の起動は既存ウィンドウを前面に出して終了します。

### 登録したキーの読み出し

```bash
# keyctl コマンドで
keyctl pipe $(keyctl search @u user my_api_key)

# Python から
import keyutils
serial = keyutils.request_key(b'my_api_key', keyutils.KEY_SPEC_USER_KEYRING)
value = keyutils.read_key(serial).decode()
```

キーリングの内容はログアウト・再起動で消去されます（揮発性）。

## 依存関係

| パッケージ | Portage | 用途 |
|---|---|---|
| Python 3 | `dev-lang/python` | 実行環境 |
| GTK 4 + PyGObject | `dev-python/pygobject` | GUI |
| python-keyutils | `dev-python/keyutils` | キーリング操作 |

Gentoo での導入：

```bash
emerge dev-python/pygobject dev-python/keyutils
```
