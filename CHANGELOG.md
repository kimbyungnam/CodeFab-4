## 0.5.0 (2026-07-07)

### Feat

- 리뷰 반영. assemble(source) 인자로 받도록 변경
- Assembler 진입점 구현 및 실객체 기반 단위 테스트 통합

## 0.4.3 (2026-07-07)

### Fix

- 한글 코드 매핑 추가하였습니다.

## 0.4.2 (2026-07-07)

### Refactor

- statement 테스트에 소급 적용

## 0.4.1 (2026-07-07)

### Refactor

- Expr 중복 코드 통합

## 0.4.0 (2026-07-07)

### Feat

- statement 52page
- statement_parser 추가

### Fix

- 새로운 main 에 맞춰 고치기

## 0.3.1 (2026-07-07)

### Refactor

- 한글 문법 변경

## 0.3.0 (2026-07-07)

### Feat

- 이중 중첩문에 대해서 기능 추가 완료
- 반복문에 대해서 테스트 완료

## 0.2.0 (2026-07-07)

### Feat

- 다른 스코프에서는 동일한 변수명 재선언 허용 테스트/통과 코드 구현 추가

## 0.1.0 (2026-07-07)

### Feat

- failing case 추가
- first commit

### Refactor

- Mock 대신에 실제 Tokenizer를 import해서 executor_unit.py 구성.
- 리팩토링 진행

## 0.0.1 (2026-07-07)

### Feat

- 변수_중복_선언_에러_검출, 지역_변수_초기화_시_자기_참조_에러_검출 코드 구현
- 변수 중복 선언 에러 검출 테스트 통과 코드 구현
- 정상 입력 확인 테스트 구현
- 변수_중복_선언_에러_검출, 지역_변수_초기화_시_자기_참조_에러_검출 코드 구현
- 변수 중복 선언 에러 검출 테스트 통과 코드 구현
- assembler expression_parser 기능 개발
- tokenizer 구현 및 테스트
- if문에 대해서 executor unit 적용 완료
- executor_unit.py first commit
- ast_nodes 인터페이스 추가
- 선언 전 사용 에러 검출 테스트 통과 코드 구현
- token
- Add project initial configurations

### Fix

- codefab.token => codefab.tokens 수정
- 버그 수정 (test_token.py -> test_tokens.py)
- 버그 수정 (token.py -> tokens.py)
- 버그수정(token.py->tokens.py)

### Refactor

- pytest fixture 이용 테스트 가독성 향상
- 선언 전 사용 에러 검출 테스트 Mocker 사용
