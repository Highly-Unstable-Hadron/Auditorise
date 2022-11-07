       IDENTIFICATION DIVISION.
           PROGRAM-ID. AUDITORISE-CORE.
      * This program converts an image (flattened 256 * 256 * 3 Numpy
      * array written into '__inout__/in.txt') into another array
      * which can be played by the speaker.

      * 4^4 = 256
      * 256^2 = 65536
      * LOG_4(65536) = 8
       >>SET CONSTANT img-len AS 256
       >>SET CONSTANT sqr AS 65536
       >>SET CONSTANT lvl-num AS 8
      * 256/8 = 32
       >>SET CONSTANT num-bands AS 8
       >>SET CONSTANT band-range AS 32
      * 65536*9 = 589824
       >>SET CONSTANT max-aud-len AS 589824
       >>SET CONSTANT numbit-16 AS 65536
       >>SET CONSTANT numsbit-16 AS 32768

       DATA DIVISION.
       WORKING-STORAGE SECTION.
       01 IMG.
           02 L-IMG OCCURS img-len TIMES.
               03 PIXEL OCCURS img-len TIMES.
                   04 RED PICTURE 999 VALUE IS 0.
                   04 FILLER PICTURE X VALUE IS SPACE.
                   04 GREEN PICTURE 999 VALUE IS 0.
                   04 FILLER PICTURE X VALUE IS SPACE.
                   04 BLUE PICTURE 999 VALUE IS 0.

       01 FLATTENED-IMG.
           02 FLAT-PIXEL OCCURS sqr TIMES.
               03 FLAT-R PICTURE 999 VALUE IS 0.
               03 FLAT-G PICTURE 999 VALUE IS 0.
               03 FLAT-B PICTURE 999 VALUE IS 0.

       01 AUD.
           02 AUD-VAL OCCURS max-aud-len TIMES USAGE IS BINARY-INT
               VALUE IS 0.

       01 STRAIGHT-VECTOR IS GLOBAL.
              02 I PICTURE S9 VALUE 1.
              02 J PICTURE S9 VALUE 0.

       01 POS-VECTOR.
              02 X USAGE IS BINARY-SHORT UNSIGNED VALUE IS 0.
              02 Y USAGE IS BINARY-SHORT UNSIGNED VALUE IS 1.
       01 POS-SCALAR USAGE IS BINARY-INT UNSIGNED VALUE IS 1.

       01 INDEX-VAR-I USAGE IS BINARY-INT UNSIGNED VALUE IS 1.
       01 INDEX-VAR-J USAGE IS BINARY-INT UNSIGNED VALUE IS 1.

       01 INDEX-AUD USAGE IS BINARY-INT UNSIGNED VALUE IS 1.
       01 INDEX-VAR-K USAGE IS BINARY-INT UNSIGNED.
       01 INDEX-VAR-L USAGE IS BINARY-INT UNSIGNED.
       01 INDEX-VAR-M USAGE IS BINARY-INT UNSIGNED.

       01 BLUE-LEVEL USAGE IS BINARY-INT SIGNED.
       01 GREEN-LEVEL USAGE IS BINARY-INT SIGNED.

       01 TL USAGE IS PROGRAM-POINTER.
       01 TR USAGE IS PROGRAM-POINTER.
       01 TEMP USAGE IS PROGRAM-POINTER.

       01 NESTING-LEVEL USAGE IS BINARY-INT UNSIGNED VALUE IS lvl-num.

       PROCEDURE DIVISION.
           PERFORM READ-INTO-MEM

           SET TL TO ENTRY 'TURN-LEFT'
           SET TR TO ENTRY 'TURN-RIGHT'
           PERFORM FORWARDS
           PERFORM HILBERT-MAP

           PERFORM DECOMPOSE-RGB

           PERFORM VARYING INDEX-VAR-M FROM 1 BY 1
           UNTIL INDEX-VAR-M IS EQUAL TO INDEX-AUD
               DISPLAY AUD-VAL(INDEX-VAR-M)
           END-PERFORM

           MOVE INDEX-AUD TO RETURN-CODE
           STOP RUN.
       READ-INTO-MEM SECTION.
      * READS INPUT ARRAY INTO MEMORY
           PERFORM WITH TEST AFTER
           VARYING INDEX-VAR-I FROM 1 BY 1 UNTIL INDEX-VAR-I = img-len

           PERFORM WITH TEST AFTER
           VARYING INDEX-VAR-J FROM 1 BY 1 UNTIL INDEX-VAR-J = img-len
               ACCEPT PIXEL(INDEX-VAR-I, INDEX-VAR-J) FROM STDIN
      *         DISPLAY PIXEL(INDEX-VAR-I, INDEX-VAR-J)
           END-PERFORM

           END-PERFORM.
       DECOMPOSE-RGB SECTION.
      * FINAL STEP
           PERFORM VARYING INDEX-VAR-K FROM 1 BY 1
           UNTIL INDEX-VAR-K IS EQUAL TO sqr
      *    RED = (numbit-16*FLAT-R(INDEX-VAR-K)/band-range)-numsbit-16
               MULTIPLY FLAT-R(INDEX-VAR-K) BY numbit-16
                   GIVING AUD-VAL(INDEX-AUD)
               DIVIDE band-range INTO AUD-VAL(INDEX-AUD)
               SUBTRACT numsbit-16 FROM AUD-VAL(INDEX-AUD)

      *    GREEN = (numbit-16 / 4) * FLAT-G(INDEX-VAR-K) / band-range
               DIVIDE 4 INTO numbit-16 GIVING GREEN-LEVEL
               MULTIPLY FLAT-G(INDEX-VAR-K) BY GREEN-LEVEL
               DIVIDE band-range INTO GREEN-LEVEL

      *    BLUE = FLAT-B(INDEX-VAR-K) / band-range
               DIVIDE band-range INTO FLAT-B(INDEX-VAR-K)
                   GIVING BLUE-LEVEL
               IF BLUE-LEVEL IS ZERO
                   ADD 1 TO BLUE-LEVEL
               END-IF
      *          DISPLAY INDEX-VAR-K ': ' AUD-VAL(INDEX-AUD) ' '
      *              BLUE-LEVEL ' ' GREEN-LEVEL ' ; ' FLAT-R(INDEX-VAR-K)
      *              ' ' FLAT-B(INDEX-VAR-K) ' ' FLAT-G(INDEX-VAR-K)
      *          END-DISPLAY

               MOVE AUD-VAL(INDEX-AUD) TO AUD-VAL(INDEX-AUD + 1)
               ADD 1 TO INDEX-AUD

               PERFORM WITH TEST BEFORE
               VARYING INDEX-VAR-L FROM INDEX-AUD BY 1
               UNTIL INDEX-VAR-L = (BLUE-LEVEL + INDEX-AUD)
                   MOVE AUD-VAL(INDEX-AUD) TO AUD-VAL(INDEX-VAR-L)
                   ADD GREEN-LEVEL TO AUD-VAL(INDEX-VAR-L)
                   MULTIPLY GREEN-LEVEL BY -1 GIVING GREEN-LEVEL
               END-PERFORM

               ADD 1 TO INDEX-AUD
           END-PERFORM
           SUBTRACT 1 FROM INDEX-AUD.
       HILBERT-MAP SECTION.
      * KEEP RECURSIVELY CALLING HILBERT-MAP UNTIL NESTING-LEVEL = 0
           IF NESTING-LEVEL IS NOT ZERO
               SUBTRACT 1 FROM NESTING-LEVEL
               CALL TR
      *        FLIP TR AND TL BEFORE CALLING HILBERT-MAP
               PERFORM FLIP-POINTERS
               PERFORM HILBERT-MAP
               PERFORM FLIP-POINTERS

               PERFORM FORWARDS
               CALL TL
               PERFORM HILBERT-MAP
               PERFORM FORWARDS
               PERFORM HILBERT-MAP
               CALL TL
               PERFORM FORWARDS

               PERFORM FLIP-POINTERS
               PERFORM HILBERT-MAP
               PERFORM FLIP-POINTERS

               CALL TR
               ADD 1 TO NESTING-LEVEL
           END-IF.
       FORWARDS SECTION.
      * COPY PIXEL OF IMG TO FLAT-PIXEL OF FLATTENED-IMG
      * AND INCREMENT INDEX
           ADD I TO X
           ADD J TO Y
           MOVE RED(Y, X) TO FLAT-R(POS-SCALAR)
           MOVE GREEN(Y, X) TO FLAT-G(POS-SCALAR)
           MOVE BLUE(Y, X) TO FLAT-B(POS-SCALAR)
           ADD 1 TO POS-SCALAR.
       FLIP-POINTERS SECTION.
           MOVE TL TO TEMP
           MOVE TR TO TL
           MOVE TEMP TO TR.

       IDENTIFICATION DIVISION.
       PROGRAM-ID. TURN-LEFT.
      * MADE NESTED PROGRAMS SO THAT POINTERS CAN BE ASSIGNED TO THEM
       PROCEDURE DIVISION.
           IF I IS NOT ZERO
               MULTIPLY I BY -1 GIVING J
               MOVE 0 TO I
           ELSE
               MOVE J TO I
               MOVE 0 TO J
           END-IF
           GOBACK.
       END PROGRAM TURN-LEFT.

       IDENTIFICATION DIVISION.
       PROGRAM-ID. TURN-RIGHT.
       PROCEDURE DIVISION.
           IF J IS NOT ZERO
               MULTIPLY J BY -1 GIVING I
               MOVE 0 TO J
           ELSE
               MOVE I TO J
               MOVE 0 TO I
           END-IF
           GOBACK.
       END PROGRAM TURN-RIGHT.

       END PROGRAM AUDITORISE-CORE.
