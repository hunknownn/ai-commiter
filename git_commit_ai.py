#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys
import git
import argparse
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain.chains import LLMChain
from langchain.prompts import PromptTemplate

def get_git_diff(repo_path='.', staged=True):
    """
    Git 저장소에서 변경 내용을 가져옵니다.
    
    Args:
        repo_path (str): Git 저장소 경로
        staged (bool): 스테이지된 변경사항만 포함할지 여부
    
    Returns:
        str: Git diff 출력
    """
    try:
        repo = git.Repo(repo_path)
        if staged:
            # 스테이지된 변경사항
            diff = repo.git.diff('--staged')
        else:
            # 모든 변경사항
            diff = repo.git.diff()
        
        # 변경된 파일 목록
        if staged:
            changed_files = repo.git.diff('--staged', '--name-only').split('\n')
        else:
            changed_files = repo.git.diff('--name-only').split('\n')
        
        # 변경 내용이 없는 경우
        if not diff:
            return None, []
        
        return diff, [f for f in changed_files if f]
    except git.exc.InvalidGitRepositoryError:
        print(f"오류: '{repo_path}'는 유효한 Git 저장소가 아닙니다.")
        sys.exit(1)
    except Exception as e:
        print(f"Git diff 가져오기 오류: {str(e)}")
        sys.exit(1)

def generate_commit_message(diff, files, prompt_template=None, openai_model="gpt-3.5-turbo"):
    """
    변경 내용을 기반으로 커밋 메시지를 생성합니다.
    
    Args:
        diff (str): Git diff 내용
        files (list): 변경된 파일 목록
        prompt_template (str, optional): 커스텀 프롬프트 템플릿
        openai_model (str, optional): 사용할 OpenAI 모델
    
    Returns:
        str: 생성된 커밋 메시지
    """
    # API 키 확인
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("오류: OPENAI_API_KEY 환경 변수가 설정되지 않았습니다.")
        sys.exit(1)
    
    # 기본 프롬프트 템플릿 설정
    if prompt_template is None:
        prompt_template = """
        다음은 Git 저장소의 변경 내용입니다. 이 변경 내용을 바탕으로 간결하고 명확한 커밋 메시지를 작성해 주세요.
        커밋 메시지는 다음과 같은 형식으로 작성해 주세요:
        - 첫 줄: 변경의 요약 (타입: 내용) - 영어로 작성
        - 두 번째 줄: 비움
        - 세 번째 줄 이후: 필요한 경우 변경 내용 상세 설명 (선택 사항)
        
        타입은 다음 중 하나를 사용하세요:
        - feat: 새로운 기능 추가
        - fix: 버그 수정
        - docs: 문서 변경
        - style: 코드 형식 변경 (코드 작동에 영향을 주지 않는 변경)
        - refactor: 코드 리팩토링
        - test: 테스트 코드 추가 또는 수정
        - chore: 빌드 프로세스 또는 보조 도구 및 라이브러리 변경
        
        변경된 파일:
        {files}
        
        변경 내용 (diff):
        {diff}
        
        커밋 메시지만 출력해주세요:
        """
    
    # LangChain 설정
    llm = ChatOpenAI(temperature=0.5, model_name=openai_model)
    chain_prompt = PromptTemplate(input_variables=["diff", "files"], template=prompt_template)
    chain = LLMChain(llm=llm, prompt=chain_prompt)
    
    # 파일 목록을 문자열로 변환
    files_str = "\n".join(files)
    
    # 너무 큰 diff는 잘라내기 (토큰 한도 고려)
    if len(diff) > 4000:
        diff = diff[:4000] + "\n... (생략됨)"
    
    # 커밋 메시지 생성
    result = chain.invoke({"diff": diff, "files": files_str})
    commit_message = result["text"] if isinstance(result, dict) and "text" in result else result
    return commit_message.strip()

def make_commit(repo_path='.', message=None):
    """
    생성된 메시지로 커밋을 수행합니다.
    
    Args:
        repo_path (str): Git 저장소 경로
        message (str): 커밋 메시지
    """
    try:
        repo = git.Repo(repo_path)
        repo.git.commit('-m', message)
        print(f"✅ 성공적으로 커밋했습니다: '{message}'")
        return True
    except Exception as e:
        print(f"커밋 오류: {str(e)}")
        return False

def main():
    # .env 파일 로드
    load_dotenv()
    
    # 명령줄 인자 파싱
    parser = argparse.ArgumentParser(description='AI를 활용한 Git 커밋 메시지 생성기')
    parser.add_argument('--repo', default='.', help='Git 저장소 경로 (기본값: 현재 디렉토리)')
    parser.add_argument('--all', action='store_false', dest='staged', 
                        help='스테이지된 변경사항 대신 모든 변경사항 포함')
    parser.add_argument('--model', default='gpt-3.5-turbo', help='사용할 OpenAI 모델')
    parser.add_argument('--commit', action='store_true', help='자동으로 커밋 수행')
    parser.add_argument('--prompt', help='커스텀 프롬프트 템플릿 파일 경로')
    
    args = parser.parse_args()
    
    # 커스텀 프롬프트 템플릿 로드
    custom_prompt = None
    if args.prompt:
        try:
            with open(args.prompt, 'r', encoding='utf-8') as f:
                custom_prompt = f.read()
        except Exception as e:
            print(f"프롬프트 파일 로드 오류: {str(e)}")
            sys.exit(1)
    
    # Git diff 가져오기
    diff, changed_files = get_git_diff(args.repo, args.staged)
    
    if diff is None or not changed_files:
        print("변경된 내용이 없습니다.")
        sys.exit(0)
    
    # 커밋 메시지 생성
    print("🤖 AI가 커밋 메시지를 생성 중입니다...")
    commit_message = generate_commit_message(diff, changed_files, custom_prompt, args.model)
    
    print("\n📝 생성된 커밋 메시지:")
    print("-" * 50)
    print(commit_message)
    print("-" * 50)
    
    # 자동 커밋 옵션이 활성화된 경우
    if args.commit:
        confirm = input("\n이 메시지로 커밋하시겠습니까? (y/n): ")
        if confirm.lower() == 'y':
            make_commit(args.repo, commit_message)
    else:
        print("\n커밋하려면 다음 명령을 실행하세요:")
        print(f"git commit -m \"{commit_message}\"")

if __name__ == "__main__":
    main()
