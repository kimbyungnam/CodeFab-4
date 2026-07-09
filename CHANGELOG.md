## 0.28.1 (2026-07-09)

### Fix

- isolate imported_paths per class method scope, like block scopes

## 0.28.0 (2026-07-09)

### Feat

- Visitor 인터페이스 도입 및 Checker/ExecutorUnit이 이를 상속하도록 변경

## 0.27.3 (2026-07-09)

### Fix

- ruff format chg2
- ruff format chg
- connect optimizing

## 0.27.2 (2026-07-09)

### Refactor

- _consume가 ParseError 서브클래스를 직접 사용하도록 통일

## 0.27.1 (2026-07-09)

### Fix

- 디버그 버그 수정

## 0.27.0 (2026-07-09)

### Feat

- CLI/REPL/debug 진입점에 함수 지원 파이프라인 배선

### Fix

- 클래스 메서드 내부 반환이 ReturnSignal을 흘려 에러로 오인 처리되는 문제 수정
- 함수 파이프라인 배선으로 해결된 known-gap xfail 테스트 정리
- FunctionChecker.visit_return_stmt이 생성자 반환 금지 검사를 우회하던 문제 수정
- 클래스 메서드 내부의 반환을 함수 외부 에러로 오판하는 문제 수정
- 함수 파이프라인에서 클래스/일반 함수 호출 시 NotCallableError 오발생 수정

## 0.26.0 (2026-07-09)

### Fix

- x =, a(세미콜론 없음) 같은 애매한 케이스는 더 이상 특별 취급 안 하고 즉시 에러
- 만약 아니면 수정
- 멀티라인 (만약 아니면 수정)
- 멀티라인 추가 및 관련 테스트 코드 추가

## 0.25.0 (2026-07-09)

### Feat

- 소문자 this와 super는 나(This), 부모(Super)의 기능을 수행하지 않도록 코드 수정. 테스트 코드도 올렸음.

### Refactor

- this도 This와 나 와 동일한 기능을 했던 부분 수정.

## 0.24.0 (2026-07-08)

### Feat

- import 실행 단계 연결 (Module 값, Get 평가)

### Fix

- Qucik start 와 Install 중복 제거

### Refactor

- README.md 수정

## 0.23.0 (2026-07-08)

### Feat

- 클래스 생성자에서 반환을 하면 에러 발생

### Refactor

- 불필요한 class 선언 제거 및 리팩토링

## 0.22.0 (2026-07-08)

### Feat

- import 실행 단계 연결 (Module 값, Get 평가)

## 0.21.1 (2026-07-08)

### Refactor

- 불필요한 class 선언 제거 및 리팩토링

## 0.21.0 (2026-07-08)

### Feat

- 순환 import 검사와 활성 스코프 체인 중복 import 검사 추가 (5b)
- import 대상 파일 로딩과 선언-only 내용 검증 추가 (5a)

## 0.20.1 (2026-07-08)

### Refactor

- 'instanceof' 대신에 '타입확인'이 default이기 때문에 .md 파일도 수정.
- instanceof 에 해당하는 타입확인 키워드 추가.

## 0.20.0 (2026-07-08)

### Feat

- mocker 기반 test double 활용한 unittest 추가
- optimizer 분기 및 depth 중첩 unittest 추가
- optimize 기능 개발

## 0.19.0 (2026-07-08)

### Feat

- import 문에 대한 스코프/루프 정적 검사 추가

## 0.18.0 (2026-07-08)

### Feat

- 디버깅 모드에서 'exit' or 'quit' 누르면 종료되는 기능 추가
- 디버깅모드 구현
- DebugRunner 추가 및 테스트 코드 추가

### Fix

- 배열 줄 오류 수정
- '>' 추가
- 디버그 라인번호 출력을 위해 line번호 저장 수정

## 0.17.0 (2026-07-08)

### Feat

- 정렬 문제 해결
- 병합 문제 해결
- 중복 클래스 제거
- 클래스 요구사항에 대해서만 기능 구현. 불필요하고, 요구받지 않는 기능은 삭제.
- 중복지정된 변수 및 함수 제거
- 클래스 기능 추가
- 클래스 요구사항에 대해서만 기능 구현. 불필요하고, 요구받지 않는 기능은 삭제.
- 중복지정된 변수 및 함수 제거
- 클래스 기능 추가

## 0.16.0 (2026-07-08)

### Feat

- pr feedback 반영 및 langauge.md 내용 추가
- array 기능 추가2
- array 기능 추가1

## 0.15.0 (2026-07-08)

### Feat

- import 문 파싱 지원

## 0.14.0 (2026-07-08)

### Feat

- repl model 수정 및 동작 방식 변경

### Fix

- class 이름 변경
- REPL 프롬프트 줄바꿈 제거에 맞춰 통합 테스트 수정
- 실행 명령을 codefab 으로 변경

## 0.13.0 (2026-07-08)

### Feat

- function 기능 추가

## 0.12.0 (2026-07-08)

### Feat

- import 문법을 위한 토큰 추가

## 0.11.1 (2026-07-07)

### Refactor

- type hint 추가_ ANY TYPE 제거

## 0.11.0 (2026-07-07)

### Feat

- 파일을 실행하는 CLI 추가

## 0.10.0 (2026-07-07)

### Feat

- **repl**: stdin을 읽어 실행하는 콘솔 스크립트 진입점 추가
- **repl**: add Repl orchestration layer using Interpreter

## 0.9.0 (2026-07-07)

### Feat

- checker 검출 책임 범위 밖 에러 구현 삭제

## 0.8.2 (2026-07-07)

### Fix

- != 에러 수정하였습니다.

## 0.8.1 (2026-07-07)

### Fix

- 소수점 파싱 버그 수정

## 0.8.0 (2026-07-07)

### Feat

- 테스트 공백 보완 및 통과 코드 구현

## 0.7.0 (2026-07-07)

### Feat

- add Interpreter orchestration layer

### Fix

- interpreter가 통합된 codefab.error.ParseError를 사용하도록 수정
- interpreter가 통합된 codefab.error 모듈의 예외 계층을 사용하도록 수정
- interpreter가 ExecutorRuntimeError의 message 속성 대신 str(exc)를 사용하도록 수정

### Refactor

- interpreter의 _format_error에서 isinstance 분기 제거

## 0.6.3 (2026-07-07)

### Refactor

- assembler/errors 모듈 error 모듈로 통합

## 0.6.2 (2026-07-07)

### Refactor

- error 모듈 통합

## 0.6.1 (2026-07-07)

### Fix

- !, != 추가 하였습니다.
- 문자열 STRING 파싱 추가 및 테스트 추가
- >=, ==, <= 로직 추가

## 0.6.0 (2026-07-07)

### Feat

- test 함수 는 -> 은으로 변경
- logical 부분 추가

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
