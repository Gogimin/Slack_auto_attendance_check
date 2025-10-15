"""
EXE 빌드 스크립트
PyInstaller를 사용하여 독립 실행 가능한 .exe 파일 생성
"""
import os
import sys
import subprocess
import shutil
from pathlib import Path

def print_step(step, total, message):
    """단계 출력"""
    print(f"\n[{step}/{total}] {message}")
    print("-" * 50)

def main():
    print("=" * 50)
    print("슬랙 출석체크 EXE 빌드")
    print("=" * 50)

    # 1. Python 버전 확인
    print_step(1, 5, "Python 버전 확인")
    print(f"Python {sys.version}")

    # 2. PyInstaller 확인
    print_step(2, 5, "PyInstaller 확인")
    try:
        import PyInstaller
        print(f"PyInstaller {PyInstaller.__version__} 설치됨")
    except ImportError:
        print("PyInstaller가 설치되지 않았습니다. 설치 중...")
        subprocess.run([sys.executable, "-m", "pip", "install", "pyinstaller"], check=True)
        print("PyInstaller 설치 완료!")

    # 3. 기존 빌드 정리
    print_step(3, 5, "기존 빌드 파일 정리")
    for folder in ["dist", "build"]:
        if Path(folder).exists():
            shutil.rmtree(folder)
            print(f"{folder}/ 삭제 완료")

    # 4. EXE 빌드
    print_step(4, 5, "EXE 파일 빌드 중...")
    print("잠시만 기다려주세요 (약 1-2분 소요)...")
    print()

    try:
        result = subprocess.run(
            [sys.executable, "-m", "PyInstaller", "attendance_app.spec", "--clean"],
            check=True,
            capture_output=False
        )

        # 5. 빌드 완료
        print_step(5, 5, "빌드 완료!")
        print()
        print("=" * 50)
        print("빌드 성공!")
        print("=" * 50)
        print()
        print("생성된 파일 위치:")
        print(f"  {Path('dist/슬랙출석체크/슬랙출석체크.exe').absolute()}")
        print()
        print("실행 방법:")
        print("  1. dist/슬랙출석체크 폴더를 원하는 위치로 복사")
        print("  2. 슬랙출석체크.exe 더블클릭")
        print()
        print("workspaces 폴더도 함께 포함되어 있습니다!")
        print("=" * 50)

    except subprocess.CalledProcessError as e:
        print()
        print("=" * 50)
        print("빌드 실패!")
        print("=" * 50)
        print(f"오류: {e}")
        print()
        print("문제 해결:")
        print("  1. requirements.txt의 모든 패키지가 설치되어 있는지 확인")
        print("  2. pip install -r requirements.txt 실행")
        print("  3. 다시 시도")
        return 1

    return 0

if __name__ == "__main__":
    try:
        exit_code = main()
        input("\n완료! 아무 키나 누르면 종료됩니다...")
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n\n빌드가 취소되었습니다.")
        sys.exit(1)
    except Exception as e:
        print(f"\n예상치 못한 오류: {e}")
        input("\n아무 키나 누르면 종료됩니다...")
        sys.exit(1)
