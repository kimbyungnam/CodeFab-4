from codefab.function_interpreter import create_function_interpreter


def interpret(source: str):
    return create_function_interpreter().interpret(source)


def test_함수_선언_호출_반환_예제():
    # docs/함수_클래스_배열_가져오기_테스트.md 1번 예제
    source = """
    함수 add(a, b) {
        반환 a + b;
    }

    변수 ret = add(3, 7);
    출력 ret;
    """

    result = interpret(source)

    assert result.error is None
    assert result.output == ["10"]


def test_재귀_호출로_팩토리얼을_계산한다():
    source = """
    함수 fact(n) {
        만약 (n <= 1) 반환 1;
        반환 n * fact(n - 1);
    }
    출력 fact(5);
    """

    result = interpret(source)

    assert result.error is None
    assert result.output == ["120"]


def test_인자없이_호출하는_함수도_동작한다():
    source = """
    함수 hello() {
        출력 "hi";
    }
    hello();
    """

    result = interpret(source)

    assert result.error is None
    assert result.output == ["hi"]


def test_여러_함수를_선언하고_서로_호출할_수_있다():
    source = """
    함수 double(x) {
        반환 x * 2;
    }
    함수 quadruple(x) {
        반환 double(double(x));
    }
    출력 quadruple(3);
    """

    result = interpret(source)

    assert result.error is None
    assert result.output == ["12"]


def test_함수_외부에서_반환을_사용하면_에러():
    source = "반환 5;"

    result = interpret(source)

    assert result.output == []
    assert "함수 외부에서는 '반환'을 사용할 수 없습니다." in result.error


def test_파라미터_이름이_중복되면_에러():
    source = "함수 foo(a, a) { 반환 a; }"

    result = interpret(source)

    assert "파라미터 이름이 중복되었습니다." in result.error


def test_함수가_아닌_대상을_호출하면_에러():
    source = """
    변수 x = "hello";
    x();
    """

    result = interpret(source)

    assert "호출 가능한 대상(함수)이 아닙니다." in result.error


def test_인자_개수가_일치하지_않으면_에러():
    source = """
    함수 foo(a, b, c) {
        반환 a;
    }
    foo(1, 2);
    """

    result = interpret(source)

    assert "인자 개수가 일치하지 않습니다" in result.error
    assert "필요: 3개" in result.error
    assert "전달: 2개" in result.error


def test_영어_키워드로도_함수를_선언하고_호출할_수_있다():
    # func/return 도 함수/반환과 동일하게 동작해야 한다 (테스트케이스.md 관례)
    source = """
    func add(a, b) {
        return a + b;
    }
    print add(1, 2);
    """

    result = interpret(source)

    assert result.error is None
    assert result.output == ["3"]
