import pandas as pd

# --- 1. 그룹 번호(숫자)와 스타일 태그(문자) 매핑 정의 ---
# 재현님이 확정한 최종 스타일 태그를 딕셔너리 형태로 정의합니다.
tag_mapping = {
    0: '[안정형 일반주]',
    1: '[고효율 우량주]',
    2: '[초고배당 가치주]',
    3: '[고위험 저평가주]',
    4: '[고성장 기대주]',
    5: '[초대형 우량주]',
    6: '[초저평가 가치주]',
    7: '[고가치 성장주]'
}

# --- 2. 최종 태그 결과 파일 로드 ---
input_file = 'stockit_ai_tags_final_v1.csv'
try:
    df = pd.read_csv(input_file, encoding='utf-8')
    print(f"로드 성공: {input_file}")
except Exception as e:
    print(f"파일 로드 실패: {e}")
    exit()

# --- 3. 태그 매핑 적용 (핵심 로직) ---
# Pandas의 .map() 함수를 사용하여 'group_tag' 컬럼의 숫자를 문자로 대체합니다.
# 새로운 컬럼을 만들어 최종 결과물로 사용할 것입니다.
df['final_style_tag'] = df['group_tag'].map(tag_mapping)

print("✅ 숫자 태그를 최종 스타일 태그로 변환 완료.")

# --- 4. 최종 파일 저장 및 확인 ---
# 기존 파일을 덮어쓰지 않고, 새로운 파일을 만들어 최종 산출물로 사용합니다.
final_output_file = 'stockit_final_tagged_data.csv'
df.to_csv(final_output_file, index=False, encoding='utf-8')

print(f"--- 최종 결과 저장 완료: {final_output_file} ---")
print("✅ 이 파일이 프로젝트 1단계의 최종 산출물입니다.")