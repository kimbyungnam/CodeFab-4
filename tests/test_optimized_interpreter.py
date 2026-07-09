from codefab.pipeline import create_optimized_interpreter


def interpret(source: str):
    return create_optimized_interpreter().interpret(source)


def test_중첩_블록에서_지역변수를_정적_바인딩으로_읽고_쓴다():
    source = """
    {
        var a = 0;
        {
            a = a + 1;
            print a;
        }
    }
    """

    result = interpret(source)

    assert result.error is None
    assert result.output == ["1"]


def test_for문_반복이_정상_동작한다():
    source = """
    for (var i = 0; i < 3; i = i + 1) {
        print i;
    }
    """

    result = interpret(source)

    assert result.error is None
    assert result.output == ["0", "1", "2"]


def test_상수_연산이_접혀도_실행_결과는_동일하다():
    source = "print 1 + 2 * 3;"

    result = interpret(source)

    assert result.error is None
    assert result.output == ["7"]


def test_0으로_나누는_상수식은_여전히_런타임_에러다():
    source = "print 1 / 0;"

    result = interpret(source)

    assert result.output == []
    assert "0으로 나눈" in result.error


def test_정적_배열_읽기_쓰기가_최적화_파이프라인에서도_동작한다():
    source = """
    var arr = Array(3);
    arr[0] = 10;
    arr[1] = 20;
    print arr[0] + arr[1];
    """

    result = interpret(source)

    assert result.error is None
    assert result.output == ["30"]


def test_자기참조_검증은_최적화_파이프라인에서도_그대로_동작한다():
    source = "var a = a + 1;"

    result = interpret(source)

    assert result.output == []
    assert "자기 참조" in result.error
