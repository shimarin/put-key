#!/usr/bin/env python3
"""put-key.py <keyname> — カーネルキーリング（@u）にシークレットを登録する GUI ツール"""

import sys
import gi

gi.require_version("Gtk", "4.0")
from gi.repository import Gtk, Gdk, GLib


def store_key(key_name: str, value: str) -> None:
    import keyutils
    keyutils.add_key(key_name.encode(), value.encode(), keyutils.KEY_SPEC_USER_KEYRING)


def on_copy_clicked(button: Gtk.Button, key_name: str, window: Gtk.Window, focus_widget: Gtk.Widget) -> None:
    clipboard = window.get_display().get_clipboard()
    clipboard.set(key_name)
    button.set_icon_name("object-select-symbolic")
    button.set_tooltip_text("コピーしました")
    def restore():
        button.set_icon_name("edit-copy-symbolic")
        button.set_tooltip_text("キー名をクリップボードにコピー")
        return False
    GLib.timeout_add(1500, restore)
    focus_widget.grab_focus()


def main() -> None:
    if len(sys.argv) != 2:
        print(f"Usage: {sys.argv[0]} <keyname>", file=sys.stderr)
        sys.exit(1)

    key_name = sys.argv[1]

    # キー名をD-Busアプリケーションid用にサニタイズ（英数字・ハイフン以外はアンダースコアに）
    safe_name = "".join(c if c.isalnum() or c == "-" else "_" for c in key_name)
    app_id = f"io.github.put_key.k_{safe_name}"

    app = Gtk.Application(application_id=app_id)
    # 同一app_idのインスタンスが既に存在する場合、GtkApplicationが前面に出して
    # 2つ目のプロセスは即終了する（デフォルト動作）

    exit_code = [1]  # キャンセル扱いをデフォルトとし、登録成功時に 0 にする

    def on_activate(app: Gtk.Application) -> None:
        # 既にウィンドウがある場合（2つ目の起動によるactivate再送）は前面に出すだけ
        existing = app.get_windows()
        if existing:
            existing[0].present()
            return

        win = Gtk.ApplicationWindow(application=app, title="秘密情報の登録")
        win.set_resizable(False)

        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        box.set_margin_top(20)
        box.set_margin_bottom(20)
        box.set_margin_start(24)
        box.set_margin_end(24)

        # 説明ラベル
        label = Gtk.Label(label=f"キーリング項目にセットするシークレット(パスワード等)を入力してください:")
        label.set_wrap(True)
        label.set_xalign(0)
        box.append(label)

        # パスワード入力欄（コピーボタンのフォーカス移動先として先に生成）
        entry = Gtk.PasswordEntry()
        entry.set_show_peek_icon(True)

        # キー名行（ラベル + リードオンリーエントリ + コピーボタン）
        key_row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        key_row.set_valign(Gtk.Align.CENTER)

        key_label = Gtk.Label(label="項目名:")
        key_label.set_xalign(0)
        key_row.append(key_label)

        key_entry = Gtk.Entry()
        key_entry.set_text(key_name)
        key_entry.set_editable(False)
        key_entry.set_can_focus(True)
        key_entry.add_css_class("monospace")
        key_entry.set_hexpand(True)
        key_row.append(key_entry)

        copy_btn = Gtk.Button()
        copy_btn.set_icon_name("edit-copy-symbolic")
        copy_btn.set_tooltip_text("キー名をクリップボードにコピー")
        copy_btn.connect("clicked", on_copy_clicked, key_name, win, entry)
        key_row.append(copy_btn)

        box.append(key_row)
        box.append(entry)

        # エラーラベル（非表示で確保）
        error_label = Gtk.Label(label="")
        error_label.add_css_class("error")
        error_label.set_xalign(0)
        box.append(error_label)

        # ボタン行
        button_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        button_box.set_halign(Gtk.Align.END)

        cancel_btn = Gtk.Button(label="キャンセル")
        cancel_btn.connect("clicked", lambda _: app.quit())
        button_box.append(cancel_btn)

        ok_btn = Gtk.Button(label="OK")
        ok_btn.add_css_class("suggested-action")
        button_box.append(ok_btn)

        box.append(button_box)

        def commit(value: str) -> None:
            try:
                store_key(key_name, value)
                exit_code[0] = 0
                app.quit()
            except Exception as e:
                error_label.set_text(f"登録失敗: {e}")

        def do_ok(_widget=None) -> None:
            value = entry.get_text()
            if value:
                commit(value)
                return
            # 空の場合は確認ダイアログ
            dlg = Gtk.AlertDialog()
            dlg.set_message("空の内容で登録しますか？")
            dlg.set_detail(f"キー「{key_name}」に空の値を登録しようとしています。")
            dlg.set_buttons(["キャンセル", "登録する"])
            dlg.set_cancel_button(0)
            dlg.set_default_button(0)
            def on_response(dlg, result, _=None):
                if dlg.choose_finish(result) == 1:
                    commit(value)
            dlg.choose(win, None, on_response)

        ok_btn.connect("clicked", do_ok)
        entry.connect("activate", do_ok)  # Enter キーでも確定

        # CSS でエラーラベルを赤く
        css = Gtk.CssProvider()
        css.load_from_string("label.error { color: red; }")
        Gtk.StyleContext.add_provider_for_display(
            win.get_display(), css, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
        )

        win.set_child(box)
        win.present()
        entry.grab_focus()

    app.connect("activate", on_activate)
    app.run([])
    sys.exit(exit_code[0])


if __name__ == "__main__":
    main()
