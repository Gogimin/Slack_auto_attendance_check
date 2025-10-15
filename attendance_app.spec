# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['app_flask.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('templates', 'templates'),
        ('static', 'static'),
        ('src', 'src'),
        ('workspaces', 'workspaces'),
    ],
    hiddenimports=[
        'flask',
        'flask.json',
        'flask.templating',
        'jinja2',
        'jinja2.ext',
        'werkzeug',
        'werkzeug.routing',
        'werkzeug.serving',
        'click',
        'itsdangerous',
        'slack_sdk',
        'slack_sdk.web',
        'slack_sdk.errors',
        'google.oauth2',
        'google.oauth2.service_account',
        'google.auth',
        'google.auth.transport',
        'googleapiclient',
        'googleapiclient.discovery',
        'google.auth.transport.requests',
        'google_auth_httplib2',
        'httplib2',
        'pandas',
        'colorlog',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='슬랙출석체크',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True,  # 콘솔 창 표시 (종료하려면 Ctrl+C)
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,  # 아이콘 파일이 있으면 여기에 경로 추가
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='슬랙출석체크',
)
