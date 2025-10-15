"""
빌드된 EXE 파일 실행 스크립트
"""
import subprocess
import sys
from pathlib import Path

def main():
    print("=" * 50)
    print("슬랙출석체크 EXE 실행")
    print("=" * 50)
    print()

    # EXE 파일 경로
    exe_path = Path("dist/슬랙출석체크/슬랙출석체크.exe")

    # EXE 파일 존재 확인
    if not exe_path.exists():
        print(f"❌ EXE 파일을 찾을 수 없습니다: {exe_path.absolute()}")
        print()
        print("먼저 빌드.bat을 실행하세요!")
        input("\n아무 키나 누르면 종료됩니다...")
        return 1

    print(f"✓ EXE 파일 찾음: {exe_path.absolute()}")
    print()
    print("EXE 실행 중...")
    print("-" * 50)
    print()

    try:
        # EXE 실행
        result = subprocess.run(
            [str(exe_path.absolute())],
            cwd=exe_path.parent,  # EXE가 있는 폴더에서 실행
            check=False
        )

        print()
        print("-" * 50)
        print(f"EXE 종료 (종료 코드: {result.returncode})")

        if result.returncode != 0:
            print()
            print("⚠️ 비정상 종료되었습니다.")
            print("오류가 발생했을 수 있습니다.")

    except Exception as e:
        print()
        print("=" * 50)
        print("❌ 실행 오류!")
        print("=" * 50)
        print(f"오류: {e}")

    input("\n아무 키나 누르면 종료됩니다...")
    return 0

if __name__ == "__main__":
    sys.exit(main())
