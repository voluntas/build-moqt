#!/usr/bin/env python3
"""
build-moqt: iOS/Android 向け MOQT 依存ライブラリビルドスクリプト

ビルド対象:
- libmsquic (QUIC プロトコル実装)
- nghttp3 (HTTP/3 ライブラリ)
- nghttp2 (HTTP/2 ライブラリ)
"""

import argparse
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

try:
    import cmake
except ImportError:
    print(
        "Error: cmake package is required. Install with: uv add cmake", file=sys.stderr
    )
    sys.exit(1)

# cmake バイナリのパス (PyPI cmake パッケージを使用)
CMAKE_BIN = Path(cmake.CMAKE_BIN_DIR) / "cmake"
if not CMAKE_BIN.exists():
    print(f"Error: cmake binary not found at {CMAKE_BIN}", file=sys.stderr)
    sys.exit(1)

# プロジェクトルート
PROJECT_ROOT = Path(__file__).parent.resolve()

# 依存ライブラリディレクトリ
DEPS_DIR = PROJECT_ROOT / "_deps"
SOURCE_DIR = DEPS_DIR / "source"
BUILD_DIR = DEPS_DIR / "build"
INSTALL_DIR = DEPS_DIR / "install"

# Toolchain ファイル
IOS_TOOLCHAIN = PROJECT_ROOT / "cmake" / "ios.toolchain.cmake"

# iOS ターゲット設定
# (ディレクトリ名, PLATFORM値)
IOS_TARGETS = [
    ("device-arm64", "OS64"),
    ("simulator-arm64", "SIMULATORARM64"),
]


def load_deps() -> dict:
    """deps.json を読み込む"""
    deps_file = PROJECT_ROOT / "deps.json"
    with open(deps_file) as f:
        return json.load(f)


def run_cmd(cmd: list[str], cwd: Path | None = None) -> None:
    """コマンドを実行"""
    print(f"+ {' '.join(cmd)}")
    subprocess.run(cmd, cwd=cwd, check=True)


def run_cmake(args: list[str], cwd: Path | None = None) -> None:
    """cmake コマンドを実行"""
    cmd = [str(CMAKE_BIN)] + args
    run_cmd(cmd, cwd)


def clone_or_update(name: str, info: dict) -> Path:
    """deps.json からソースを取得"""
    source_dir = SOURCE_DIR / name

    if not source_dir.exists():
        print(f"\n=== Cloning {name} ===")
        url = info["url"]
        SOURCE_DIR.mkdir(parents=True, exist_ok=True)
        run_cmd(["git", "clone", url, str(source_dir)])

    # tag または ref にチェックアウト
    ref = info.get("tag") or info.get("ref")
    if ref:
        print(f"Checking out {name} @ {ref}")
        run_cmd(["git", "fetch", "--all", "--tags"], cwd=source_dir)
        run_cmd(["git", "checkout", ref], cwd=source_dir)

    # submodule 初期化
    run_cmd(
        ["git", "submodule", "update", "--init", "--recursive", "--depth", "1"],
        cwd=source_dir,
    )

    return source_dir


def fetch_sources(deps: dict, libraries: list[str]) -> dict[str, Path]:
    """指定されたライブラリのソースを取得"""
    sources = {}
    for name in libraries:
        if name in deps:
            sources[name] = clone_or_update(name, deps[name])
    return sources


def get_build_dir(platform: str, target: str, build_type: str, lib_name: str) -> Path:
    """ビルドディレクトリを取得"""
    return BUILD_DIR / platform / target / build_type / lib_name


def get_install_dir(platform: str, target: str, build_type: str) -> Path:
    """インストールディレクトリを取得"""
    return INSTALL_DIR / platform / target / build_type


def build_msquic_ios(
    source_dir: Path, target: str, platform: str, build_type: str
) -> None:
    """iOS 向け msquic をビルド"""
    build_dir = get_build_dir("ios", target, build_type, "msquic")
    install_dir = get_install_dir("ios", target, build_type)

    build_dir.mkdir(parents=True, exist_ok=True)

    cmake_args = [
        "-S",
        str(source_dir),
        "-B",
        str(build_dir),
        f"-DCMAKE_TOOLCHAIN_FILE={IOS_TOOLCHAIN}",
        f"-DPLATFORM={platform}",
        "-DDEPLOYMENT_TARGET=13.0",
        "-DENABLE_BITCODE=OFF",
        f"-DCMAKE_BUILD_TYPE={build_type}",
        f"-DCMAKE_INSTALL_PREFIX={install_dir}",
        "-DQUIC_BUILD_SHARED=OFF",
        "-DQUIC_TLS_LIB=quictls",
        "-DQUIC_BUILD_TOOLS=OFF",
        "-DQUIC_BUILD_TEST=OFF",
        "-DQUIC_BUILD_PERF=OFF",
    ]

    run_cmake(cmake_args)
    run_cmake(["--build", str(build_dir), "--parallel"])
    run_cmake(["--install", str(build_dir)])


def build_nghttp3_ios(
    source_dir: Path, target: str, platform: str, build_type: str
) -> None:
    """iOS 向け nghttp3 をビルド"""
    build_dir = get_build_dir("ios", target, build_type, "nghttp3")
    install_dir = get_install_dir("ios", target, build_type)

    build_dir.mkdir(parents=True, exist_ok=True)

    cmake_args = [
        "-S",
        str(source_dir),
        "-B",
        str(build_dir),
        f"-DCMAKE_TOOLCHAIN_FILE={IOS_TOOLCHAIN}",
        f"-DPLATFORM={platform}",
        "-DDEPLOYMENT_TARGET=13.0",
        "-DENABLE_BITCODE=OFF",
        f"-DCMAKE_BUILD_TYPE={build_type}",
        f"-DCMAKE_INSTALL_PREFIX={install_dir}",
        "-DENABLE_LIB_ONLY=ON",
        "-DENABLE_STATIC_LIB=ON",
        "-DENABLE_SHARED_LIB=OFF",
        "-DBUILD_TESTING=OFF",
    ]

    run_cmake(cmake_args)
    run_cmake(["--build", str(build_dir), "--parallel"])
    run_cmake(["--install", str(build_dir)])


def build_nghttp2_ios(
    source_dir: Path, target: str, platform: str, build_type: str
) -> None:
    """iOS 向け nghttp2 をビルド"""
    build_dir = get_build_dir("ios", target, build_type, "nghttp2")
    install_dir = get_install_dir("ios", target, build_type)

    build_dir.mkdir(parents=True, exist_ok=True)

    cmake_args = [
        "-S",
        str(source_dir),
        "-B",
        str(build_dir),
        f"-DCMAKE_TOOLCHAIN_FILE={IOS_TOOLCHAIN}",
        f"-DPLATFORM={platform}",
        "-DDEPLOYMENT_TARGET=13.0",
        "-DENABLE_BITCODE=OFF",
        f"-DCMAKE_BUILD_TYPE={build_type}",
        f"-DCMAKE_INSTALL_PREFIX={install_dir}",
        "-DENABLE_LIB_ONLY=ON",
        "-DBUILD_STATIC_LIBS=ON",
        "-DBUILD_SHARED_LIBS=OFF",
        "-DBUILD_TESTING=OFF",
    ]

    run_cmake(cmake_args)
    run_cmake(["--build", str(build_dir), "--parallel"])
    run_cmake(["--install", str(build_dir)])


def build_msquic_android(source_dir: Path, arch: str, build_type: str) -> None:
    """Android 向け msquic をビルド"""
    ndk_home = os.environ.get("ANDROID_NDK_HOME")
    if not ndk_home:
        raise RuntimeError("ANDROID_NDK_HOME environment variable is not set")

    toolchain = Path(ndk_home) / "build" / "cmake" / "android.toolchain.cmake"

    build_dir = get_build_dir("android", arch, build_type, "msquic")
    install_dir = get_install_dir("android", arch, build_type)

    build_dir.mkdir(parents=True, exist_ok=True)

    cmake_args = [
        "-S",
        str(source_dir),
        "-B",
        str(build_dir),
        f"-DCMAKE_TOOLCHAIN_FILE={toolchain}",
        f"-DANDROID_ABI={arch}",
        "-DANDROID_PLATFORM=android-29",
        f"-DCMAKE_BUILD_TYPE={build_type}",
        f"-DCMAKE_INSTALL_PREFIX={install_dir}",
        "-DQUIC_BUILD_SHARED=OFF",
        "-DQUIC_TLS_LIB=quictls",
        "-DQUIC_BUILD_TOOLS=OFF",
        "-DQUIC_BUILD_TEST=OFF",
        "-DQUIC_BUILD_PERF=OFF",
    ]

    run_cmake(cmake_args)
    run_cmake(["--build", str(build_dir), "--parallel"])
    run_cmake(["--install", str(build_dir)])


def build_nghttp3_android(source_dir: Path, arch: str, build_type: str) -> None:
    """Android 向け nghttp3 をビルド"""
    ndk_home = os.environ.get("ANDROID_NDK_HOME")
    if not ndk_home:
        raise RuntimeError("ANDROID_NDK_HOME environment variable is not set")

    toolchain = Path(ndk_home) / "build" / "cmake" / "android.toolchain.cmake"

    build_dir = get_build_dir("android", arch, build_type, "nghttp3")
    install_dir = get_install_dir("android", arch, build_type)

    build_dir.mkdir(parents=True, exist_ok=True)

    cmake_args = [
        "-S",
        str(source_dir),
        "-B",
        str(build_dir),
        f"-DCMAKE_TOOLCHAIN_FILE={toolchain}",
        f"-DANDROID_ABI={arch}",
        "-DANDROID_PLATFORM=android-29",
        f"-DCMAKE_BUILD_TYPE={build_type}",
        f"-DCMAKE_INSTALL_PREFIX={install_dir}",
        "-DENABLE_LIB_ONLY=ON",
        "-DENABLE_STATIC_LIB=ON",
        "-DENABLE_SHARED_LIB=OFF",
        "-DBUILD_TESTING=OFF",
    ]

    run_cmake(cmake_args)
    run_cmake(["--build", str(build_dir), "--parallel"])
    run_cmake(["--install", str(build_dir)])


def build_nghttp2_android(source_dir: Path, arch: str, build_type: str) -> None:
    """Android 向け nghttp2 をビルド"""
    ndk_home = os.environ.get("ANDROID_NDK_HOME")
    if not ndk_home:
        raise RuntimeError("ANDROID_NDK_HOME environment variable is not set")

    toolchain = Path(ndk_home) / "build" / "cmake" / "android.toolchain.cmake"

    build_dir = get_build_dir("android", arch, build_type, "nghttp2")
    install_dir = get_install_dir("android", arch, build_type)

    build_dir.mkdir(parents=True, exist_ok=True)

    cmake_args = [
        "-S",
        str(source_dir),
        "-B",
        str(build_dir),
        f"-DCMAKE_TOOLCHAIN_FILE={toolchain}",
        f"-DANDROID_ABI={arch}",
        "-DANDROID_PLATFORM=android-29",
        f"-DCMAKE_BUILD_TYPE={build_type}",
        f"-DCMAKE_INSTALL_PREFIX={install_dir}",
        "-DENABLE_LIB_ONLY=ON",
        "-DBUILD_STATIC_LIBS=ON",
        "-DBUILD_SHARED_LIBS=OFF",
        "-DBUILD_TESTING=OFF",
    ]

    run_cmake(cmake_args)
    run_cmake(["--build", str(build_dir), "--parallel"])
    run_cmake(["--install", str(build_dir)])


def build_ios(
    sources: dict[str, Path], libraries: list[str], build_types: list[str]
) -> None:
    """iOS 向けビルドを実行"""
    for target, platform in IOS_TARGETS:
        for build_type in build_types:
            print(f"\n=== Building iOS {target} ({build_type}) ===\n")

            if "msquic" in libraries and "msquic" in sources:
                print(f"Building msquic for iOS {target} ({build_type})...")
                build_msquic_ios(sources["msquic"], target, platform, build_type)

            if "nghttp3" in libraries and "nghttp3" in sources:
                print(f"Building nghttp3 for iOS {target} ({build_type})...")
                build_nghttp3_ios(sources["nghttp3"], target, platform, build_type)

            if "nghttp2" in libraries and "nghttp2" in sources:
                print(f"Building nghttp2 for iOS {target} ({build_type})...")
                build_nghttp2_ios(sources["nghttp2"], target, platform, build_type)


def create_xcframework(libraries: list[str], build_types: list[str]) -> None:
    """xcframework を作成"""
    xcframework_dir = INSTALL_DIR / "xcframework"
    xcframework_dir.mkdir(parents=True, exist_ok=True)

    for build_type in build_types:
        for lib_name in libraries:
            lib_file = f"lib{lib_name}.a"
            output = xcframework_dir / build_type / f"{lib_name}.xcframework"

            # 既存の xcframework を削除
            if output.exists():
                shutil.rmtree(output)

            output.parent.mkdir(parents=True, exist_ok=True)

            # xcodebuild コマンド構築
            cmd = ["xcodebuild", "-create-xcframework"]

            for target, _ in IOS_TARGETS:
                install_dir = get_install_dir("ios", target, build_type)
                lib_path = install_dir / "lib" / lib_file
                include_path = install_dir / "include"

                if not lib_path.exists():
                    print(f"Warning: {lib_path} not found, skipping...")
                    continue

                cmd.extend(["-library", str(lib_path)])
                if include_path.exists():
                    cmd.extend(["-headers", str(include_path)])

            cmd.extend(["-output", str(output)])

            print(f"\n=== Creating {lib_name}.xcframework ({build_type}) ===")
            run_cmd(cmd)

            print(f"Created: {output}")


def build_android(
    sources: dict[str, Path], libraries: list[str], build_types: list[str]
) -> None:
    """Android 向けビルドを実行"""
    archs = ["arm64-v8a", "x86_64"]

    for arch in archs:
        for build_type in build_types:
            print(f"\n=== Building Android {arch} ({build_type}) ===\n")

            if "msquic" in libraries and "msquic" in sources:
                print(f"Building msquic for Android {arch} ({build_type})...")
                build_msquic_android(sources["msquic"], arch, build_type)

            if "nghttp3" in libraries and "nghttp3" in sources:
                print(f"Building nghttp3 for Android {arch} ({build_type})...")
                build_nghttp3_android(sources["nghttp3"], arch, build_type)

            if "nghttp2" in libraries and "nghttp2" in sources:
                print(f"Building nghttp2 for Android {arch} ({build_type})...")
                build_nghttp2_android(sources["nghttp2"], arch, build_type)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Build MOQT dependencies for iOS/Android"
    )
    parser.add_argument(
        "--platform",
        choices=["ios", "android", "all"],
        default="ios",
        help="Target platform (default: ios)",
    )
    parser.add_argument(
        "--build-type",
        choices=["release", "debug", "all"],
        default="all",
        help="Build type (default: all)",
    )
    parser.add_argument(
        "--library",
        choices=["msquic", "nghttp3", "nghttp2", "all"],
        default="all",
        help="Library to build (default: all)",
    )
    parser.add_argument(
        "--clean",
        action="store_true",
        help="Clean build directory before building",
    )
    parser.add_argument(
        "--clean-all",
        action="store_true",
        help="Clean all (source, build, install) before building",
    )
    parser.add_argument(
        "--xcframework",
        action="store_true",
        help="Create xcframework after building (iOS only)",
    )
    parser.add_argument(
        "--xcframework-only",
        action="store_true",
        help="Create xcframework only (skip building)",
    )
    parser.add_argument(
        "--fetch-only",
        action="store_true",
        help="Fetch sources only (skip building)",
    )

    args = parser.parse_args()

    # ライブラリリスト
    if args.library == "all":
        libraries = ["msquic", "nghttp3", "nghttp2"]
    else:
        libraries = [args.library]

    # ビルドタイプリスト
    if args.build_type == "all":
        build_types = ["Release", "Debug"]
    elif args.build_type == "release":
        build_types = ["Release"]
    else:
        build_types = ["Debug"]

    # クリーン
    if args.clean_all and DEPS_DIR.exists():
        print(f"Cleaning {DEPS_DIR}...")
        shutil.rmtree(DEPS_DIR)
    elif args.clean:
        if BUILD_DIR.exists():
            print(f"Cleaning {BUILD_DIR}...")
            shutil.rmtree(BUILD_DIR)
        if INSTALL_DIR.exists():
            print(f"Cleaning {INSTALL_DIR}...")
            shutil.rmtree(INSTALL_DIR)

    # deps.json を読み込み
    deps = load_deps()
    print("Dependencies:")
    for name, info in deps.items():
        version = info.get("tag") or info.get("ref", "unknown")[:8]
        print(f"  {name}: {version}")
    print()

    # ビルド実行
    try:
        # xcframework のみ作成
        if args.xcframework_only:
            create_xcframework(libraries, build_types)
            print("\n=== xcframework created successfully ===\n")
            return 0

        # ソース取得
        sources = fetch_sources(deps, libraries)

        # fetch のみ
        if args.fetch_only:
            print("\n=== Sources fetched successfully ===\n")
            return 0

        if args.platform in ("ios", "all"):
            build_ios(sources, libraries, build_types)

            if args.xcframework:
                create_xcframework(libraries, build_types)

        if args.platform in ("android", "all"):
            build_android(sources, libraries, build_types)

        print("\n=== Build completed successfully ===\n")
        return 0

    except subprocess.CalledProcessError as e:
        print(f"\nBuild failed: {e}", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"\nError: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
