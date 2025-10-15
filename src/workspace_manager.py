"""
워크스페이스 관리자
여러 슬랙 워크스페이스 설정을 관리하는 모듈
"""
import json
from pathlib import Path
from typing import Dict, List, Optional


class WorkspaceConfig:
    """워크스페이스 설정 클래스"""

    def __init__(self, workspace_path: Path):
        """
        Args:
            workspace_path: 워크스페이스 폴더 경로
        """
        self.path = workspace_path
        self.name = workspace_path.name

        # 설정 파일 경로
        self.config_file = workspace_path / "config.json"
        self.credentials_file = workspace_path / "credentials.json"

        # 설정 로드
        self._config = self._load_config()

    def _load_config(self) -> Dict:
        """config.json 로드"""
        if not self.config_file.exists():
            raise FileNotFoundError(f"설정 파일을 찾을 수 없습니다: {self.config_file}")

        with open(self.config_file, 'r', encoding='utf-8') as f:
            return json.load(f)

    def is_valid(self) -> bool:
        """워크스페이스 설정이 유효한지 확인"""
        required_files = [self.config_file, self.credentials_file]

        # 필수 파일 확인
        for file in required_files:
            if not file.exists():
                return False

        # 필수 키 확인
        required_keys = [
            'slack_bot_token',
            'slack_channel_id',
            'spreadsheet_id',
            'sheet_name',
            'name_column',
            'start_row'
        ]

        for key in required_keys:
            if key not in self._config:
                return False

        return True

    @property
    def display_name(self) -> str:
        """화면에 표시할 이름"""
        return self._config.get('name', self.name)

    @property
    def slack_bot_token(self) -> str:
        return self._config['slack_bot_token']

    @property
    def slack_channel_id(self) -> str:
        return self._config['slack_channel_id']

    @property
    def spreadsheet_id(self) -> str:
        return self._config['spreadsheet_id']

    @property
    def sheet_name(self) -> str:
        return self._config['sheet_name']

    @property
    def name_column(self) -> int:
        return self._config['name_column']

    @property
    def start_row(self) -> int:
        return self._config['start_row']

    @property
    def credentials_path(self) -> str:
        return str(self.credentials_file)


class WorkspaceManager:
    """워크스페이스 관리 클래스"""

    def __init__(self, base_dir: Optional[Path] = None):
        """
        Args:
            base_dir: 프로젝트 루트 디렉토리 (기본값: 현재 파일 기준 상위 디렉토리)
        """
        if base_dir is None:
            base_dir = Path(__file__).parent.parent

        self.base_dir = base_dir
        self.workspaces_dir = base_dir / "workspaces"

        # workspaces 폴더가 없으면 생성
        self.workspaces_dir.mkdir(exist_ok=True)

    def get_all_workspaces(self) -> List[WorkspaceConfig]:
        """모든 워크스페이스 설정 가져오기"""
        workspaces = []

        if not self.workspaces_dir.exists():
            return workspaces

        # workspaces 폴더 내의 모든 하위 폴더 탐색
        for item in self.workspaces_dir.iterdir():
            if item.is_dir():
                try:
                    workspace = WorkspaceConfig(item)
                    if workspace.is_valid():
                        workspaces.append(workspace)
                except Exception as e:
                    print(f"⚠️ 워크스페이스 로드 실패 ({item.name}): {e}")

        # 이름순으로 정렬
        workspaces.sort(key=lambda x: x.display_name)

        return workspaces

    def get_workspace(self, name: str) -> Optional[WorkspaceConfig]:
        """특정 워크스페이스 가져오기"""
        workspace_path = self.workspaces_dir / name

        if not workspace_path.exists():
            return None

        try:
            workspace = WorkspaceConfig(workspace_path)
            if workspace.is_valid():
                return workspace
        except Exception as e:
            print(f"⚠️ 워크스페이스 로드 실패 ({name}): {e}")

        return None

    def get_workspace_names(self) -> List[str]:
        """모든 워크스페이스 이름 리스트"""
        return [ws.display_name for ws in self.get_all_workspaces()]


# 테스트 코드
if __name__ == '__main__':
    manager = WorkspaceManager()

    print("📁 사용 가능한 워크스페이스:")
    workspaces = manager.get_all_workspaces()

    if not workspaces:
        print("  ⚠️ 워크스페이스가 없습니다.")
        print("  workspaces/ 폴더에 워크스페이스를 추가하세요.")
    else:
        for ws in workspaces:
            print(f"  ✓ {ws.display_name}")
            print(f"    - 채널 ID: {ws.slack_channel_id}")
            print(f"    - 스프레드시트: {ws.spreadsheet_id}")
            print()
