[![codecov](https://codecov.io/gh/kimbyungnam/CodeFab-4/graph/badge.svg?token=SJ40GY81IP)](https://codecov.io/gh/kimbyungnam/CodeFab-4)

# CodeFab-4
CodeFab Interpreter 프로젝트

## Quick Start

| 구분 | 명령 |
|---|---|
| 설치 | 👉 [Install](#install) 참고 |
| REPL 모드 실행 | `(.venv) codefab` |
| 파일 모드 실행 | `(.venv) codefab run <스크립트경로>` |
| 디버그 모드 실행 | `(.venv) codefab debug <스크립트경로>` |

`(.venv)`는 venv를 활성화한 상태(터미널 프롬프트 앞에 실제로 붙는 표시)에서 실행해야 한다는
뜻입니다 — `codefab` 명령어 자체가 설치 과정에서 venv 안에 생성되기 때문에, venv를 활성화하지
않은 터미널에서는 실행되지 않습니다.

아래는 각 단계의 상세 설명입니다.

## Install

가상환경(venv)을 만들고, 그 안에서 설치합니다.

**cmd (Windows)**
```cmd
python -m venv .venv
.venv\Scripts\activate.bat
python -m pip install flit
flit install -s
```

**PowerShell (Windows)**
```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install flit
flit install -s
```

**Git Bash / macOS / Linux**
```bash
python -m venv .venv
source .venv/Scripts/activate   # macOS/Linux는 source .venv/bin/activate
python -m pip install flit
flit install -s
```

`flit install -s`를 실행하면 venv 안에 `codefab` 명령어가 설치됩니다. 이후 작업은 venv를
활성화한 상태(프롬프트 앞에 `(.venv)`가 붙은 상태)에서 진행하면 되고, 빠져나올 때는
`deactivate`를 입력합니다.

## How to use

`codefab`은 서브커맨드로 모드를 선택합니다.

### REPL 모드 (인자 없이 실행)

```bash
codefab
```

한 줄씩 입력하면 즉시 실행되고, `exit` 또는 `quit`을 입력하면 종료됩니다.

### 파일 모드 (`run` 서브커맨드)

```bash
codefab run <스크립트경로>
```

스크립트 파일을 한 번에 읽어 실행합니다.

### 디버그 모드 (`debug` 서브커맨드)

```bash
codefab debug <스크립트경로>
```

Stmt(문장) 단위로 멈춰가며 실행 상태를 점검합니다. 정지 상태에서 아래 명령을 입력할 수 있습니다.

| 명령 | 설명 |
|---|---|
| `step` | 현재 Stmt 실행 후 다음 Stmt에서 정지 |
| `next` | 현재 Stmt 실행 (블록/반복문 내부로는 진입하지 않음) |
| `break <줄번호>` | 해당 줄에 breakpoint 설정 |
| `breakpoints` | 설정된 breakpoint 목록 출력 |
| `remove <줄번호>` | breakpoint 해제 |
| `continue` | 다음 breakpoint까지 실행 |
| `watch <변수명>` | 정지할 때마다 해당 변수 값을 자동으로 출력 |
| `unwatch <변수명>` | 감시 목록에서 제거 |
| `watches` | 감시 중인 변수 목록과 값 출력 |
| `inspect` | 현재 스코프의 모든 변수와 값(타입 포함) 출력 |
| `exit` / `quit` | 디버그 세션 종료 |

## 언어 문법 (Laugh Language)

CodeFab이 실행하는 커스텀 언어(코드명 "Laugh Language")의 문법을 소개합니다. 모든 문장은
`;`으로 끝냅니다.

> 내부적으로는 영문 키워드(`var`, `true`, `func` 등)도 임의로 함께 지원되지만, 이는 팀이 정식으로
> 채택한 문법이 아니라 참고용으로 남겨둔 것이므로 이 문서에서는 다루지 않습니다. 실제 코드
> 작성 시에는 아래 한국어 키워드만 사용하세요.

### 변수

```
변수 a = 3;
변수 b = a + 1;
{
    변수 a = "블록 안에서는 새로운 a";  // 바깥의 a와는 별개 (블록 스코프)
}
a = 10;  // 재할당
```

### 자료형과 리터럴

| 종류 | 예시 | 비고 |
|---|---|---|
| 숫자 | `3`, `3.14` | 내부적으로 모두 float. 정수값은 출력 시 소수점 없이 표시(`5.0` → `5`) |
| 문자열 | `"hello"` | `+`로 연결 가능 (`"hi" + "there"` → `"hithere"`) |
| 불리언 | `참` / `거짓` | 출력하면 그대로 `참`/`거짓`로 표시 |

### 연산자

| 종류 | 연산자 |
|---|---|
| 산술 | `+ - * /` |
| 비교 | `> >= < <= == !=` |
| 논리 | `그리고`, `또는`, 단항 `!` |
| 그룹핑 | `( )` |

```
출력 1 + 2 * 3;      // 7 (곱셈이 먼저)
출력 (1 + 2) * 3;    // 9
출력 !참;            // 거짓
출력 1 != 2;         // 참
```

### 출력

```
출력 a + b;
```

### 제어문

```
만약 (x > 5) {
    출력 "big";
} 아니면 {
    출력 "small";
}

반복 (변수 i = 0; i < 3; i = i + 1) {
    출력 i;
}
```

`아니면`은 가장 가까운 `만약`에 결합합니다(dangling-else).

### 함수 (`함수`, `반환`)

```
함수 fact(n) {
    만약 (n <= 1) {
        반환 1;
    }
    반환 n * fact(n - 1);
}

출력 fact(5);  // 120
```

인자 개수가 선언과 다르면 런타임 에러가 발생합니다(`인자 개수가 일치하지 않습니다. (필요: 2개, 전달: 1개)`).
`반환;`처럼 값 없이 반환하면 파이썬의 `None`이 그대로 반환값이 되며, 이를 `출력`하면
문자열 `None`이 출력됩니다(한국어 리터럴로 통일되지 않은 부분이며, 알려진 제약사항 참고).

### 클래스 (`클래스`)

```
클래스 Robot {
    생성자(name, speed) {
        나.name = name;
        나.speed = speed;
    }
    move(dist) {
        나.speed = 나.speed + dist;
    }
    report() {
        출력 나.name;
        출력 나.speed;
    }
}

클래스 SpeedRobot : Robot {
    move(dist) {
        부모.move(dist);
        출력 "Speeeed!";
    }
}

변수 r = SpeedRobot("Sam", 10);
r.move(5);       // Speeeed!
r.report();      // Sam / 15
출력 (r 타입확인 SpeedRobot);  // 참
출력 (r 타입확인 Robot);       // 참 (부모 클래스도 성립)
```

- 필드는 `.`으로 동적으로 읽고 쓸 수 있습니다 (`r.speed = 10;`).
- `나`로 자기 인스턴스에, `부모`로 부모 클래스의 메서드에 접근합니다.
- 생성자 이름은 `생성자`입니다. 생성자 안에서는 `반환`을 사용할 수 없습니다.
- `:`로 상속을 표기합니다 (`클래스 자식 : 부모 { ... }`).
- `타입확인`은 부모 클래스에 대해서도 `참`을 반환합니다.

### 정적 배열 (`배열`)

```
변수 arr = 배열(3);  // [null, null, null]
arr[0] = 10;
arr[1] = 20;
arr[2] = 30;
출력 arr[0];  // 10
```

### 모듈 가져오기 (`가져오기`, `별칭`)

```
가져오기 "lib_math.laugh" 별칭 math;
출력 math.pi;
```

- 가져오는 파일에는 **변수 선언(`변수`)과 다른 파일에 대한 `가져오기`만** 작성할 수 있습니다
  (함수·클래스 선언은 아직 지원하지 않습니다 — 알려진 제약사항 참고). 그 외의 문장이 있으면
  `가져온 파일 '...'에는 가져오기, 변수 선언만 작성할 수 있습니다.` 에러가 발생합니다.
- 같은 스코프에서 같은 파일을 두 번 가져오면 에러(`이미 가져온 파일입니다: '...'`)가 발생합니다.
  단, 서로 다른(형제) 스코프에서는 같은 파일을 각각 가져올 수 있습니다.
- `가져오기`끼리 서로를 순환 참조하면 에러(`순환 import가 발생했습니다: '...'`)가 발생합니다.
- 반복문(`반복`) 내부에서는 `가져오기`를 사용할 수 없습니다.

### 대표적인 런타임 에러

에러가 발생하면 `[N번째 줄] <메시지>` 형식으로 출력되고 실행이 즉시 종료됩니다. 자주 마주치는
에러의 정확한 문구:

| 상황 | 메시지 |
|---|---|
| 0으로 나누기 | `0으로 나눈 오류입니다.` |
| 정의되지 않은 변수 사용 | `정의되지 않은 변수 'x'입니다.` |
| 숫자가 아닌 값에 산술 연산 | `피연산자는 반드시 숫자여야 합니다.` |
| 배열 인덱스가 범위를 벗어남 | `배열의 인덱스 범위를 벗어났습니다.` |
| 배열이 아닌 값에 `[]` 사용 | `'[]' 연산은 배열에만 사용할 수 있습니다: '...'` |
| 존재하지 않는 필드/메서드 접근 | `정의되지 않은 필드/메서드 'x'입니다.` |
| 호출할 수 없는 대상 호출 (`"hi"()`) | `호출 가능한 대상(함수)이 아닙니다.` |

## Development

### Test

pytest 를 사용합니다
```bash
pytest tests
```

### pre-commit

pre-commit 설치
```bash
pre-commit install
```

### Commit Convention

This project follows the [Conventional Commits 1.0.0](https://www.conventionalcommits.org/en/v1.0.0/) specification.

Commit messages are validated with [Commitizen](https://commitizen-tools.github.io/commitizen/) and Git hooks are managed by [pre-commit](https://pre-commit.com/).

#### References

- [Conventional Commits 1.0.0](https://www.conventionalcommits.org/en/v1.0.0/)
- [Commitizen Documentation](https://commitizen-tools.github.io/commitizen/)
- [Commitizen - Writing Commits](https://commitizen-tools.github.io/commitizen/tutorials/writing_commits/)
- [pre-commit Documentation](https://pre-commit.com/)

### Branch Convention

작업 성격에 따라서 Branch 이름은 아래와 같이 사용합니다

1. feature : Red 테스트 와 기능 추가 작업
2. test : Test 코드만 추가 작업
3. refactoring : 기능 변경 없이 Refactoring 작업
