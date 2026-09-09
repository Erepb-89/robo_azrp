# available_trajectories.py

available_trajectories = {
    "pHomePosition": [
        "tHomePosition_To_HelicopterModule",
        "tHomePosition_To_Payload",
        "tHomePosition_To_Grippers",
        "tHomePosition_To_Charger",
        "tHomePosition_To_VTOLModule",
        "tHomePosition_To_VTOL2Charger1",
        "tHomePosition_To_VTOL2Charger2",
    ],
    "pHelicopterModule": [
        "tHelicopterModule_To_HomePosition",
        "tHelicopterModule_To_Helicopter1",
        "tHelicopterModule_To_Helicopter2",
    ],
    "pHelicopter1": [
        "tHelicopter1_To_HelicopterModule",
    ],
    "pHelicopter2": [
        "tHelicopter2_To_HelicopterModule",
        "tHelicopter2_To_Helicopter2Payload",
        "tHelicopter2_To_Helicopter2Battery1",
        "tHelicopter2_To_Helicopter2Battery2",
    ],
    "pHelicopter2Payload": [
        "tHelicopter2Payload_To_Helicopter2",
    ],
    "pHelicopter2Battery1": [
        "tHelicopter2Battery1_To_Helicopter2",
        "tHelicopter2Battery1_To_Helicopter2InsideBattery1Slot",
        "tHelicopter2Battery1_To_Helicopter2BeforeBattery1Slot",
    ],
    "pHelicopter2InsideBattery1Slot": [
        "tHelicopter2InsideBattery1Slot_To_Helicopter2Battery1",
        "tHelicopter2InsideBattery1Slot_To_Helicopter2BeforeBattery1Slot",
    ],
    "pHelicopter2BeforeBattery1Slot": [
        "tHelicopter2BeforeBattery1Slot_To_Helicopter2",
        "tHelicopter2BeforeBattery1Slot_To_Helicopter2Battery1",
        "tHelicopter2BeforeBattery1Slot_To_Helicopter2InsideBattery1Slot",
    ],
    "pHelicopter2Battery2": [
        "tHelicopter2Battery2_To_Helicopter2",
        "tHelicopter2Battery2_To_Helicopter2InsideBattery2Slot",
        "tHelicopter2Battery2_To_Helicopter2BeforeBattery2Slot",
    ],
    "pHelicopter2InsideBattery2Slot": [
        "tHelicopter2InsideBattery2Slot_To_Helicopter2Battery2",
        "tHelicopter2InsideBattery2Slot_To_Helicopter2BeforeBattery2Slot",
    ],
    "pHelicopter2BeforeBattery2Slot": [
        "tHelicopter2BeforeBattery2Slot_To_Helicopter2",
        "tHelicopter2BeforeBattery2Slot_To_Helicopter2Battery2",
        "tHelicopter2BeforeBattery2Slot_To_Helicopter2InsideBattery2Slot",
    ],
    "pPayload": [
        "tPayload_To_HomePosition",
        "tPayload_To_Payload1",
        "tPayload_To_Payload2",
    ],
    "pPayload1": [
        "tPayload1_To_Payload",
        "tPayload1_To_Payload1InsideSlot",
        "tPayload1_To_Payload1BeforeSlot",
    ],
    "pPayload1InsideSlot": [
        "tPayload1InsideSlot_To_Payload1BeforeSlot",
        "tPayload1InsideSlot_To_Payload1",
    ],
    "pPayload1BeforeSlot": [
        "tPayload1BeforeSlot_To_Payload1",
        "tPayload1BeforeSlot_To_Payload1InsideSlot",
    ],
    "pPayload2": [
        "tPayload2_To_Payload",
        "tPayload2_To_Payload2InsideSlot",
        "tPayload2_To_Payload2BeforeSlot",
    ],
    "pPayload2InsideSlot": [
        "tPayload2InsideSlot_To_Payload2BeforeSlot",
        "tPayload2InsideSlot_To_Payload2",
    ],
    "pPayload2BeforeSlot": [
        "tPayload2BeforeSlot_To_Payload2",
        "tPayload2BeforeSlot_To_Payload2InsideSlot",
    ],
    "pGrippers": [
        "tGrippers_To_HomePosition",
        "tGrippers_To_Grippers1",
        "tGrippers_To_Grippers2",
    ],
    "pGrippers1": [
        "tGrippers1_To_Grippers",
        "tGrippers1_To_Grippers1InsideSlot",
        "tGrippers1_To_Grippers1BeforeSlot",
    ],
    "pGrippers1InsideSlot": [
        "tGrippers1InsideSlot_To_Grippers1BeforeSlot",
        "tGrippers1InsideSlot_To_Grippers1",
    ],
    "pGrippers1BeforeSlot": [
        "tGrippers1BeforeSlot_To_Grippers1",
        "tGrippers1BeforeSlot_To_Grippers1InsideSlot",
    ],
    "pGrippers2": [
        "tGrippers2_To_Grippers",
        "tGrippers2_To_Grippers2InsideSlot",
        "tGrippers2_To_Grippers2BeforeSlot",
    ],
    "pGrippers2InsideSlot": [
        "tGrippers2InsideSlot_To_Grippers2BeforeSlot",
        "tGrippers2InsideSlot_To_Grippers2",
    ],
    "pGrippers2BeforeSlot": [
        "tGrippers2BeforeSlot_To_Grippers2",
        "tGrippers2BeforeSlot_To_Grippers2InsideSlot",
    ],
    "pCharger": [
        "tCharger_To_HomePosition",
        "tCharger_To_Helicopter2Charger1",
    ],
    "pHelicopter2Charger1": [
        "tHelicopter2Charger1_To_Charger",
        "tHelicopter2Charger1_To_Helicopter2Charger1Slot1",
        "tHelicopter2Charger1_To_Helicopter2Charger1Slot2",
        "tHelicopter2Charger1_To_Helicopter2Charger1BeforeSlot1",
        "tHelicopter2Charger1_To_Helicopter2Charger1Buttons",
    ],
    "pHelicopter2Charger1Slot1": [
        "tHelicopter2Charger1Slot1_To_Helicopter2Charger1",
        "tHelicopter2Charger1Slot1_To_Helicopter2Charger1InsideSlot1",
        "tHelicopter2Charger1Slot1_To_Helicopter2Charger1BeforeSlot1",
    ],
    "pHelicopter2Charger1InsideSlot1": [
        "tHelicopter2Charger1InsideSlot1_To_Helicopter2Charger1Slot1",
        "tHelicopter2Charger1InsideSlot1_To_Helicopter2Charger1BeforeSlot1",
    ],
    "pHelicopter2Charger1BeforeSlot1": [
        "tHelicopter2Charger1BeforeSlot1_To_Helicopter2Charger1",
        "tHelicopter2Charger1BeforeSlot1_To_Helicopter2Charger1InsideSlot1",
        "tHelicopter2Charger1BeforeSlot1_To_Helicopter2Charger1Slot1",
    ],
    "pHelicopter2Charger1Slot2": [
        "tHelicopter2Charger1Slot2_To_Helicopter2Charger1",
        "tHelicopter2Charger1Slot2_To_Helicopter2Charger1InsideSlot2",
        "tHelicopter2Charger1Slot2_To_Helicopter2Charger1BeforeSlot2",
    ],
    "pHelicopter2Charger1InsideSlot2": [
        "tHelicopter2Charger1InsideSlot2_To_Helicopter2Charger1Slot2",
        "tHelicopter2Charger1InsideSlot2_To_Helicopter2Charger1BeforeSlot2",
    ],
    "pHelicopter2Charger1BeforeSlot2": [
        "tHelicopter2Charger1BeforeSlot2_To_Helicopter2Charger1",
        "tHelicopter2Charger1BeforeSlot2_To_Helicopter2Charger1InsideSlot2",
        "tHelicopter2Charger1BeforeSlot2_To_Helicopter2Charger1Slot2",
    ],
    "pVTOL2Charger1": [
        "tVTOL2Charger1_To_VTOL2Charger1Slot1",
        "tVTOL2Charger1_To_VTOL2Charger1Slot2",
        "tVTOL2Charger1_To_VTOL2Charger1BeforeSlot1",
        "tVTOL2Charger1_To_HomePosition",
    ],
    "pVTOL2Charger1Slot1": [
        "tVTOL2Charger1Slot1_To_VTOL2Charger1",
        "tVTOL2Charger1Slot1_To_VTOL2Charger1InsideSlot1",
        "tVTOL2Charger1Slot1_To_VTOL2Charger1BeforeSlot1",
    ],
    "pVTOL2Charger1InsideSlot1": [
        "tVTOL2Charger1InsideSlot1_To_VTOL2Charger1Slot1",
        "tVTOL2Charger1InsideSlot1_To_VTOL2Charger1BeforeSlot1",
    ],
    "pVTOL2Charger1BeforeSlot1": [
        "tVTOL2Charger1BeforeSlot1_To_VTOL2Charger1",
        "tVTOL2Charger1BeforeSlot1_To_VTOL2Charger1InsideSlot1",
        "tVTOL2Charger1BeforeSlot1_To_VTOL2Charger1Slot1",
    ],
    "pVTOL2Charger1Slot2": [
        "tVTOL2Charger1Slot2_To_VTOL2Charger1",
        "tVTOL2Charger1Slot2_To_VTOL2Charger1InsideSlot2",
        "tVTOL2Charger1Slot2_To_VTOL2Charger1BeforeSlot2",
    ],
    "pVTOL2Charger1InsideSlot2": [
        "tVTOL2Charger1InsideSlot2_To_VTOL2Charger1Slot2",
        "tVTOL2Charger1InsideSlot2_To_VTOL2Charger1BeforeSlot2",
    ],
    "pVTOL2Charger1BeforeSlot2": [
        "tVTOL2Charger1BeforeSlot2_To_VTOL2Charger1",
        "tVTOL2Charger1BeforeSlot2_To_VTOL2Charger1InsideSlot2",
        "tVTOL2Charger1BeforeSlot2_To_VTOL2Charger1Slot2",
    ],
    "pVTOL2Charger2": [
        "tVTOL2Charger2_To_VTOL2Charger2Slot1",
        "tVTOL2Charger2_To_VTOL2Charger2Slot2",
        "tVTOL2Charger2_To_VTOL2Charger2BeforeSlot1",
        "tVTOL2Charger2_To_HomePosition",
    ],
    "pVTOL2Charger2Slot1": [
        "tVTOL2Charger2Slot1_To_VTOL2Charger2",
        "tVTOL2Charger2Slot1_To_VTOL2Charger2InsideSlot1",
        "tVTOL2Charger2Slot1_To_VTOL2Charger2BeforeSlot1",
    ],
    "pVTOL2Charger2InsideSlot1": [
        "tVTOL2Charger2InsideSlot1_To_VTOL2Charger2Slot1",
        "tVTOL2Charger2InsideSlot1_To_VTOL2Charger2BeforeSlot1",
        "tVTOL2Charger2Slot2_after_sticking_batt",
    ],
    "pVTOL2Charger2BeforeSlot1": [
        "tVTOL2Charger2BeforeSlot1_To_VTOL2Charger2",
        "tVTOL2Charger2BeforeSlot1_To_VTOL2Charger2InsideSlot1",
        "tVTOL2Charger2BeforeSlot1_To_VTOL2Charger2Slot1",
        "tVTOL2Charger2Slot1_after_ejecting",
        "tVTOL2Charger2Slot1_move_end_point_batt",
    ],
    "pVTOL2Charger2Slot2": [
        "tVTOL2Charger2Slot2_To_VTOL2Charger2",
        "tVTOL2Charger2Slot2_To_VTOL2Charger2InsideSlot2",
        "tVTOL2Charger2Slot2_To_VTOL2Charger2BeforeSlot2",
    ],
    "pVTOL2Charger2InsideSlot2": [
        "tVTOL2Charger2InsideSlot2_To_VTOL2Charger2Slot2",
        "tVTOL2Charger2InsideSlot2_To_VTOL2Charger2BeforeSlot2",
        "tVTOL2Charger2Slot1_after_sticking_batt",
    ],
    "pVTOL2Charger2BeforeSlot2": [
        "tVTOL2Charger2BeforeSlot2_To_VTOL2Charger2",
        "tVTOL2Charger2BeforeSlot2_To_VTOL2Charger2InsideSlot2",
        "tVTOL2Charger2BeforeSlot2_To_VTOL2Charger2Slot2",
        "tVTOL2Charger2Slot2_after_ejecting",
        "tVTOL2Charger2Slot2_move_end_point_batt",
    ],
    "pVTOLModule": [
        "tVTOLModule_To_HomePosition",
        "tVTOLModule_To_VTOL1",
        "tVTOLModule_To_VTOL2",
    ],
    "pVTOL1": [
        "tVTOL1_To_VTOLModule",
        "tVTOL1_To_VTOL1Payload",
    ],
    "pVTOL2": [
        "tVTOL2_To_VTOLModule",
        "tVTOL2_To_VTOL2Battery1",
        "tVTOL2_To_VTOL2Battery2",
    ],
    "pVTOL2Battery1": [
        "tVTOL2Battery1_To_VTOL2",
        "tVTOL2Battery1_To_VTOL2InsideBattery1Slot",
        "tVTOL2Battery1_To_VTOL2BeforeBattery1Slot",
    ],
    "pVTOL2InsideBattery1Slot": [
        "tVTOL2InsideBattery1Slot_To_VTOL2BeforeBattery1Slot",
        "tVTOL2InsideBattery1Slot_To_VTOL2Battery1",
    ],
    "pVTOL2BeforeBattery1Slot": [
        "tVTOL2BeforeBattery1Slot_To_VTOL2",
        "tVTOL2BeforeBattery1Slot_To_VTOL2Battery1",
        "tVTOL2BeforeBattery1Slot_To_VTOL2InsideBattery1Slot",
    ],
    "pVTOL2Battery2": [
        "tVTOL2Battery2_To_VTOL2",
        "tVTOL2Battery2_To_VTOL2InsideBattery2Slot",
        "tVTOL2Battery2_To_VTOL2BeforeBattery2Slot",
    ],
    "pVTOL2InsideBattery2Slot": [
        "tVTOL2InsideBattery2Slot_To_VTOL2BeforeBattery2Slot",
        "tVTOL2InsideBattery2Slot_To_VTOL2Battery2",
    ],
    "pVTOL2BeforeBattery2Slot": [
        "tVTOL2BeforeBattery2Slot_To_VTOL2",
        "tVTOL2BeforeBattery2Slot_To_VTOL2Battery2",
        "tVTOL2BeforeBattery2Slot_To_VTOL2InsideBattery2Slot",
    ],
    "pHelicopter2Charger1Slot1Button": [
        "tHelicopter2Charger1Slot1Button_To_Helicopter2Charger1Buttons",
    ],
    "pHelicopter2Charger1Slot2Button": [
        "tHelicopter2Charger1Slot2Button_To_Helicopter2Charger1Buttons",
    ],
    "pHelicopter2Charger1Buttons": [
        "tHelicopter2Charger1Buttons_To_Helicopter2Charger1",
        "tHelicopter2Charger1Buttons_To_Helicopter2Charger1Slot1Button",
        "tHelicopter2Charger1Buttons_To_Helicopter2Charger1Slot2Button",
    ],
}