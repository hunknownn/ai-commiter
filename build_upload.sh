#!/bin/bash

# 스크립트 중 오류 발생 시 실행 중단
set -e

# .env 파일이 존재하면 환경변수 로드
if [ -f .env ]; then
  echo "📁 .env 파일에서 환경변수를 불러오는 중..."
  export $(grep -v '^#' .env | xargs)
else
  echo "⚠️ .env 파일이 존재하지 않습니다. .env.example 파일을 참고하여 .env 파일을 생성해주세요."
  exit 1
fi

# PYPI_API_TOKEN 환경변수 확인
if [ -z "$PYPI_API_TOKEN" ]; then
  echo "⚠️ PYPI_API_TOKEN 환경변수가 설정되지 않았습니다."
  echo "  .env 파일에 PYPI_API_TOKEN=your-token-here 형식으로 추가해주세요."
  exit 1
fi

# TWINE 환경변수 설정
export TWINE_USERNAME="__token__"
export TWINE_PASSWORD="$PYPI_API_TOKEN"

echo "🧹 빌드 아티팩트 정리 중..."
rm -rf build/ dist/ *.egg-info/

echo "🔧 패키지 빌드 중..."
python3 -m build

echo "📤 PyPI에 패키지 업로드 중..."
python3 -m twine upload dist/*

echo "✅ 완료! PyPI 페이지를 확인하세요: https://pypi.org/project/ai-commiter/"

# 현재 버전 가져오기
VERSION=$(python -c "import ai_commiter; print(ai_commiter.__version__)")
echo "🏷️ 현재 버전: $VERSION"
echo "📌 Git 태그 관리:"
echo "  git tag -a v$VERSION -m \"버전 $VERSION 릴리즈\""
echo "  git push --tags"
