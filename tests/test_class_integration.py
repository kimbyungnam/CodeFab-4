"""docs/함수_클래스_배열_가져오기_테스트.md 의 클래스 관련 시나리오(2~7번)를
전체 파이프라인(Assembler -> Checker -> Executor)으로 실행해 검증한다."""

from codefab.interpreter import Interpreter


def run(source: str):
    result = Interpreter().interpret(source)
    assert result.error is None, f"예상치 못한 에러: {result.error}"
    return result.output


def test_2_클래스_선언과_인스턴스_생성():
    source = """
    클래스 Robot {
    }

    변수 robot = Robot();
    """

    assert run(source) == []


def test_3_인스턴스에_필드_동적_저장_읽기():
    source = """
    클래스 Robot {
    }

    변수 r = Robot();

    r.name = "SpeedRobot";
    r.speed = 10;

    출력 r.name;
    """

    assert run(source) == ["SpeedRobot"]


def test_4_클래스_내부_메서드와_나():
    source = """
    클래스 Robot {
        move(dist) {
            나.position = 나.position + dist;
        }

        report() {
            출력 나.position;
        }
    }

    변수 r = Robot();
    r.position = 0;
    r.move(5);
    r.report();
    """

    assert run(source) == ["5"]


def test_5_생성자():
    source = """
    클래스 Robot {
        생성자(name, speed) {
            나.name = name;
            나.speed = speed;
        }
    }

    변수 r = Robot("AndOr", 10);
    출력 r.name;
    """

    assert run(source) == ["AndOr"]


def test_6_상속과_부모_메서드_호출():
    source = """
    클래스 Robot {
        move(dist) {
            출력 "move";
        }
    }

    클래스 SpeedRobot : Robot {
        move(dist) {
            부모.move(dist);
            출력 "Speeeed!";
        }
    }

    SpeedRobot().move(3);
    """

    assert run(source) == ["move", "Speeeed!"]


def test_7_인스턴스_타입_확인():
    source = """
    클래스 Robot {
        생성자(name) {
            나.name = name;
        }
    }

    클래스 SpeedRobot : Robot {
        생성자(name) {
            부모.생성자(name);
        }
    }

    변수 w = SpeedRobot("Sam");

    출력 (w instanceof SpeedRobot);
    출력 (w instanceof Robot);
    """

    assert run(source) == ["참", "참"]
