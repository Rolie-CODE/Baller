import cv2 as cv
import mediapipe as mp

mp_hands = mp.solutions.hands
mp_draw = mp.solutions.drawing_utils

hands = mp_hands.Hands(
    max_num_hands=1,
    min_detection_confidence=0.7,
    min_tracking_confidence=0.7
)

cap = cv.VideoCapture(0)


def finger_states(hand_landmarks):
    """
    Returns which fingers are up (1) or down (0)
    """

    landmarks = hand_landmarks.landmark

    # Finger tip and pip indices
    tips = [8, 12, 16, 20]
    pips = [6, 10, 14, 18]

    fingers = []

    # Thumb (special case: compare x-axis)
    if landmarks[4].x < landmarks[3].x:
        fingers.append(1)
    else:
        fingers.append(0)

    # Other 4 fingers
    for tip, pip in zip(tips, pips):
        if landmarks[tip].y < landmarks[pip].y:
            fingers.append(1)
        else:
            fingers.append(0)

    return fingers


while True:
    ret, frame = cap.read()
    if not ret:
        break

    frame = cv.flip(frame, 1)
    rgb = cv.cvtColor(frame, cv.COLOR_BGR2RGB)

    results = hands.process(rgb)

    gesture = "No Hand"

    if results.multi_hand_landmarks:
        for hand_landmarks in results.multi_hand_landmarks:

            mp_draw.draw_landmarks(
                frame,
                hand_landmarks,
                mp_hands.HAND_CONNECTIONS
            )

            fingers = finger_states(hand_landmarks)

            # Gesture logic
            if fingers == [0, 0, 0, 0, 0]:
                gesture = "FIST (HOLD)"

            elif fingers == [1, 1, 1, 1, 1]:
                gesture = "OPEN HAND (STOP)"

            elif fingers == [0, 1, 0, 0, 0]:
                gesture = "1 POINT"

            elif fingers == [1, 0, 0, 0, 0]:
                gesture = "JUMP BALL"

            elif fingers == [0, 1, 1, 0, 0]:
                gesture = "2 POINT"

            elif fingers == [1, 1, 1, 0, 0]:
                gesture = "3 POINT"

            else:
                gesture = "UNKNOWN"

    cv.rectangle(frame, (40, 20), (300, 70), (0, 0, 0), -1)

    cv.putText(frame, gesture, (50, 55),
           cv.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 255), 2)

    cv.imshow("Basketball Gesture Recognition", frame)

    if cv.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv.destroyAllWindows()