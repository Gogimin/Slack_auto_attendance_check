"""
PNG 이미지를 ICO 파일로 변환
"""
from PIL import Image
from pathlib import Path

def convert_png_to_ico():
    """PNG를 ICO로 변환"""
    png_path = Path("img/Auto.png")
    ico_path = Path("img/Auto.ico")

    if not png_path.exists():
        print(f"❌ PNG 파일을 찾을 수 없습니다: {png_path}")
        return False

    try:
        # PNG 이미지 열기
        img = Image.open(png_path)

        # RGBA 모드로 변환
        if img.mode != 'RGBA':
            img = img.convert('RGBA')

        # 여러 크기로 ICO 생성 (Windows 권장)
        icon_sizes = [(16, 16), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)]

        # ICO 파일 저장
        img.save(
            ico_path,
            format='ICO',
            sizes=icon_sizes
        )

        print(f"✓ ICO 파일 생성 완료: {ico_path.absolute()}")
        return True

    except Exception as e:
        print(f"❌ 변환 실패: {e}")
        return False

if __name__ == "__main__":
    print("=" * 50)
    print("PNG → ICO 변환")
    print("=" * 50)
    print()

    if convert_png_to_ico():
        print()
        print("=" * 50)
        print("변환 완료!")
        print("=" * 50)
        print()
        print("다음 단계:")
        print("1. 빌드.bat 실행")
        print("2. 생성된 EXE 파일의 아이콘 확인")
    else:
        print()
        print("변환 실패. PIL(Pillow) 설치가 필요합니다:")
        print("  pip install pillow")

    input("\n아무 키나 누르면 종료됩니다...")
