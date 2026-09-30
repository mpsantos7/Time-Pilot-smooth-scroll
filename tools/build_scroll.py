"""Build a 32 KiB Time Pilot ROM with precomputed one-pixel cloud scrolling.

Input is the exact disassembly revision, verified by SHA-256. Originals and the
previous experiment remain untouched. No assembler or third-party Python module
is required: the included small Z80 assembler is used. The graphics reader is an external
dependency from https://github.com/antxiko/TimePilot-disassembly.
"""
import argparse
import hashlib
import json
import sys
import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
import z80_assembler as asm

EXPECTED = '183e80262301b18d41762d64a2fc326f4a4bef17832109225637e184d54a70d9'
ORG = 0x8000
TABLE = 0x9000
FIRST = 0x22
FRAME_BYTES = 24 * 8
# E800=x, E801=y, E802=dx, E803=dy, E804=ticks remaining,
# E812/E813=signed half-pixel velocity, E814/E815=fractional residues.
# E805=ready, E806/E807=departing edges, E809-E80C=drawing scratch,
# E80D=prepared group, E80E=pending, E80F=displayed group, E810-E811=pending cell delta. The game uses E000-E7FE and its stack grows down from E7FE.
SOURCE = '''
SNAP:
    call 4C97h
    xor a
    ld (0E805h),a
    ld (0E804h),a
    ret
RESET:
    di
    xor a
    ld (0E800h),a
    ld (0E801h),a
    ld (0E804h),a
    ld (0E806h),a
    ld (0E807h),a
    ld (0E80Dh),a
    ld (0E80Eh),a
    ld (0E80Fh),a
    ld (0E814h),a
    ld (0E815h),a
    inc a
    ld (0E805h),a
    call UPLOAD
    call DRAW
    ld hl,0E100h
    ei
    ret
ARM:
    ; Use the original sixteen-way heading BEFORE its eight-way rounding.
    ld a,(0E101h)
    and 15
    add a,a
    ld hl,DIRECTIONS
    call 4012h
    ld a,(hl)
    ld (0E812h),a
    inc hl
    ld a,(hl)
    ld (0E813h),a
    ld a,6
    ld (0E804h),a
    ret
FINE:
    ld a,(0E805h)
    or a
    jr z,DONE
    ld a,(0E050h)
    or a
    jr nz,DONE
    ld a,(0E015h)
    or a
    jr z,DONE
    ld a,(0E80Eh)
    or a
    jr z,DONE
    xor a
    ld (0E80Eh),a
    ld a,(0E810h)
    ld e,a
    ld a,(0E811h)
    ld d,a
    or e
    jr z,COMMIT_DRAW
    ld hl,0E212h
    call MOVE_CELLS
COMMIT_DRAW:
    call DRAW
    ld a,(0E80Dh)
    ld (0E80Fh),a
DONE:
    ld a,(0E050h)
    ret

; Prepare AFTER gameplay, into the group that is not currently displayed.
; The next interrupt commits the name table before running the game logic.
PREPARE:
    ld a,(0E805h)
    or a
    jr z,PREPARED
    ld a,(0E050h)
    or a
    jr nz,PREPARED
    ld a,(0E015h)
    or a
    jr z,PREPARED
    ld a,(0E80Eh)
    or a
    jr nz,PREPARED
    ld a,(0E804h)
    or a
    jr z,PREPARED
    dec a
    ld (0E804h),a
    jr z,PREPARED
    cp 3
    jr z,PREPARED
    call VELOCITY
    call STEP
PREPARED:
    ld hl,0E380h
    ret
; Signed half-pixel accumulators retain their residues across turns.
VELOCITY:
    ld a,(0E812h)
    ld b,a
    ld a,(0E814h)
    add a,b
    ld b,a
    and 1
    ld (0E814h),a
    ld a,b
    rlca
    ld a,b
    rra
    ld (0E802h),a
    ld a,(0E813h)
    ld b,a
    ld a,(0E815h)
    add a,b
    ld b,a
    and 1
    ld (0E815h),a
    ld a,b
    rlca
    ld a,b
    rra
    ld (0E803h),a
    ret
STEP:
    xor a
    ld (0E806h),a
    ld (0E807h),a
    ld de,0
    ld a,(0E802h)
    ld b,a
    ld a,(0E800h)
    add a,b
    ld c,a
    and 7
    ld (0E800h),a
    bit 3,c
    jr z,STEP_Y
    ld e,b
    ld a,b
    ld (0E806h),a
    bit 7,e
    jr z,STEP_Y
    dec d
STEP_Y:
    ld a,(0E803h)
    ld b,a
    ld a,(0E801h)
    add a,b
    ld c,a
    and 7
    ld (0E801h),a
    bit 3,c
    jr z,STEP_DRAW
    ld a,b
    ld (0E807h),a
    ld hl,32
    bit 7,b
    jr z,STEP_ADD
    ld hl,0FFE0h
STEP_ADD:
    add hl,de
    ex de,hl
STEP_DRAW:
    ld a,e
    ld (0E810h),a
    ld a,d
    ld (0E811h),a
    ld a,(0E80Fh)
    xor 1
    ld (0E80Dh),a
    call UPLOAD
    ld a,1
    ld (0E80Eh),a
    ret
UPLOAD:
    ld a,(0E801h)
    add a,a
    add a,a
    add a,a
    ld b,a
    ld a,(0E800h)
    or b
    ld l,a
    ld h,0
    add hl,hl
    ld de,POINTERS
    add hl,de
    ld a,(hl)
    inc hl
    ld h,(hl)
    ld l,a
    ld de,6110h
    ld a,(0E80Dh)
    or a
    jr z,UPLOAD_ADDRESS
    ld de,61D0h
UPLOAD_ADDRESS:
    call 4017h
    ld c,98h
    ld b,192
    outi
    nop
    nop
    nop
    outi
    nop
    nop
    nop
    outi
    nop
    nop
    nop
    outi
    nop
    nop
    nop
    outi
    nop
    nop
    nop
    outi
    nop
    nop
    nop
    outi
    nop
    nop
    nop
    outi
    nop
    nop
    nop
    outi
    nop
    nop
    nop
    outi
    nop
    nop
    nop
    outi
    nop
    nop
    nop
    outi
    nop
    nop
    nop
    outi
    nop
    nop
    nop
    outi
    nop
    nop
    nop
    outi
    nop
    nop
    nop
    outi
    nop
    nop
    nop
    outi
    nop
    nop
    nop
    outi
    nop
    nop
    nop
    outi
    nop
    nop
    nop
    outi
    nop
    nop
    nop
    outi
    nop
    nop
    nop
    outi
    nop
    nop
    nop
    outi
    nop
    nop
    nop
    outi
    nop
    nop
    nop
    outi
    nop
    nop
    nop
    outi
    nop
    nop
    nop
    outi
    nop
    nop
    nop
    outi
    nop
    nop
    nop
    outi
    nop
    nop
    nop
    outi
    nop
    nop
    nop
    outi
    nop
    nop
    nop
    outi
    nop
    nop
    nop
    outi
    nop
    nop
    nop
    outi
    nop
    nop
    nop
    outi
    nop
    nop
    nop
    outi
    nop
    nop
    nop
    outi
    nop
    nop
    nop
    outi
    nop
    nop
    nop
    outi
    nop
    nop
    nop
    outi
    nop
    nop
    nop
    outi
    nop
    nop
    nop
    outi
    nop
    nop
    nop
    outi
    nop
    nop
    nop
    outi
    nop
    nop
    nop
    outi
    nop
    nop
    nop
    outi
    nop
    nop
    nop
    outi
    nop
    nop
    nop
    outi
    nop
    nop
    nop
    outi
    nop
    nop
    nop
    outi
    nop
    nop
    nop
    outi
    nop
    nop
    nop
    outi
    nop
    nop
    nop
    outi
    nop
    nop
    nop
    outi
    nop
    nop
    nop
    outi
    nop
    nop
    nop
    outi
    nop
    nop
    nop
    outi
    nop
    nop
    nop
    outi
    nop
    nop
    nop
    outi
    nop
    nop
    nop
    outi
    nop
    nop
    nop
    outi
    nop
    nop
    nop
    outi
    nop
    nop
    nop
    outi
    nop
    nop
    nop
    outi
    nop
    nop
    nop
    outi
    nop
    nop
    nop
    outi
    nop
    nop
    nop
    outi
    nop
    nop
    nop
    outi
    nop
    nop
    nop
    outi
    nop
    nop
    nop
    outi
    nop
    nop
    nop
    outi
    nop
    nop
    nop
    outi
    nop
    nop
    nop
    outi
    nop
    nop
    nop
    outi
    nop
    nop
    nop
    outi
    nop
    nop
    nop
    outi
    nop
    nop
    nop
    outi
    nop
    nop
    nop
    outi
    nop
    nop
    nop
    outi
    nop
    nop
    nop
    outi
    nop
    nop
    nop
    outi
    nop
    nop
    nop
    outi
    nop
    nop
    nop
    outi
    nop
    nop
    nop
    outi
    nop
    nop
    nop
    outi
    nop
    nop
    nop
    outi
    nop
    nop
    nop
    outi
    nop
    nop
    nop
    outi
    nop
    nop
    nop
    outi
    nop
    nop
    nop
    outi
    nop
    nop
    nop
    outi
    nop
    nop
    nop
    outi
    nop
    nop
    nop
    outi
    nop
    nop
    nop
    outi
    nop
    nop
    nop
    outi
    nop
    nop
    nop
    outi
    nop
    nop
    nop
    outi
    nop
    nop
    nop
    outi
    nop
    nop
    nop
    outi
    nop
    nop
    nop
    outi
    nop
    nop
    nop
    outi
    nop
    nop
    nop
    outi
    nop
    nop
    nop
    outi
    nop
    nop
    nop
    outi
    nop
    nop
    nop
    outi
    nop
    nop
    nop
    outi
    nop
    nop
    nop
    outi
    nop
    nop
    nop
    outi
    nop
    nop
    nop
    outi
    nop
    nop
    nop
    outi
    nop
    nop
    nop
    outi
    nop
    nop
    nop
    outi
    nop
    nop
    nop
    outi
    nop
    nop
    nop
    outi
    nop
    nop
    nop
    outi
    nop
    nop
    nop
    outi
    nop
    nop
    nop
    outi
    nop
    nop
    nop
    outi
    nop
    nop
    nop
    outi
    nop
    nop
    nop
    outi
    nop
    nop
    nop
    outi
    nop
    nop
    nop
    outi
    nop
    nop
    nop
    outi
    nop
    nop
    nop
    outi
    nop
    nop
    nop
    outi
    nop
    nop
    nop
    outi
    nop
    nop
    nop
    outi
    nop
    nop
    nop
    outi
    nop
    nop
    nop
    outi
    nop
    nop
    nop
    outi
    nop
    nop
    nop
    outi
    nop
    nop
    nop
    outi
    nop
    nop
    nop
    outi
    nop
    nop
    nop
    outi
    nop
    nop
    nop
    outi
    nop
    nop
    nop
    outi
    nop
    nop
    nop
    outi
    nop
    nop
    nop
    outi
    nop
    nop
    nop
    outi
    nop
    nop
    nop
    outi
    nop
    nop
    nop
    outi
    nop
    nop
    nop
    outi
    nop
    nop
    nop
    outi
    nop
    nop
    nop
    outi
    nop
    nop
    nop
    outi
    nop
    nop
    nop
    outi
    nop
    nop
    nop
    outi
    nop
    nop
    nop
    outi
    nop
    nop
    nop
    outi
    nop
    nop
    nop
    outi
    nop
    nop
    nop
    outi
    nop
    nop
    nop
    outi
    nop
    nop
    nop
    outi
    nop
    nop
    nop
    outi
    nop
    nop
    nop
    outi
    nop
    nop
    nop
    outi
    nop
    nop
    nop
    outi
    nop
    nop
    nop
    outi
    nop
    nop
    nop
    outi
    nop
    nop
    nop
    outi
    nop
    nop
    nop
    outi
    nop
    nop
    nop
    outi
    nop
    nop
    nop
    outi
    nop
    nop
    nop
    outi
    nop
    nop
    nop
    outi
    nop
    nop
    nop
    outi
    nop
    nop
    nop
    outi
    nop
    nop
    nop
    outi
    nop
    nop
    nop
    outi
    nop
    nop
    nop
    outi
    nop
    nop
    nop
    outi
    nop
    nop
    nop
    outi
    nop
    nop
    nop
    outi
    nop
    nop
    nop
    outi
    nop
    nop
    nop
    outi
    nop
    nop
    nop
    outi
    nop
    nop
    nop
    outi
    nop
    nop
    nop
    outi
    nop
    nop
    nop
    outi
    nop
    nop
    nop
    outi
    nop
    nop
    nop
    outi
    nop
    nop
    nop
    outi
    nop
    nop
    nop
    outi
    nop
    nop
    nop
    outi
    nop
    nop
    nop
    outi
    nop
    nop
    nop
    outi
    nop
    nop
    nop
    outi
    nop
    nop
    nop
    outi
    nop
    nop
    nop
    outi
    nop
    nop
    nop
    outi
    nop
    nop
    nop
    outi
    nop
    nop
    nop
    outi
    nop
    nop
    nop
    ret


; Coarse transition: one rectangle writes both the new cloud and the
; outgoing edge. No separate erase pass. Descriptor index = (dy+1)*3+dx+1.
DRAW:
    ld a,1
    ld (0E22Fh),a
    ld a,(0E807h)
    inc a
    ld b,a
    add a,a
    add a,b
    ld b,a
    ld a,(0E806h)
    inc a
    add a,b
    add a,a
    add a,a
    add a,a
    ld (0E80Ah),a
    call FIND_FIRST
    ld a,(0E80Ch)
    ld l,a
    ld h,0E2h
    ld b,9
DRAW_CLOUD:
    push bc
    push hl
    ld c,(hl)
    inc hl
    ld d,(hl)
    inc hl
    ld e,(hl)
    ld a,c
    or a
    ld a,(0E80Ah)
    jr z,DRAW_DESCRIPTOR
    add a,72
DRAW_DESCRIPTOR:
    ld b,a
    ld hl,8C00h
    ld a,(0E80Dh)
    or a
    jr z,DRAW_ADDRESS
    ld hl,8E00h
DRAW_ADDRESS:
    ld a,b
    call 4012h
    ld a,(hl)
    ld (0E809h),a
    inc hl
    ld a,(hl)
    ld (0E80Bh),a
    inc hl
    ld a,(hl)
    inc hl
    or a
    call nz,NEXT_COLUMN
    ld a,(hl)
    inc hl
    or a
    call nz,NEXT_ROW
    ld a,(hl)
    inc hl
    ld h,(hl)
    ld l,a
    ld c,98h
    ld a,(0E80Bh)
    ld b,a
    ld a,(0E809h)
    cp 3
    jr z,DRAW_WIDTH3
    cp 4
    jr z,DRAW_WIDTH4
    cp 5
    jr z,DRAW_WIDTH5
    call DRAW6
    jr DRAW_NEXT
DRAW_WIDTH3:
    call DRAW3
    jr DRAW_NEXT
DRAW_WIDTH4:
    call DRAW4
    jr DRAW_NEXT
DRAW_WIDTH5:
    call DRAW5
DRAW_NEXT:
    pop hl
    inc hl
    inc hl
    inc hl
    ld a,l
    cp 2Ch
    jr nz,DRAW_MORE
    ld hl,0E211h
DRAW_MORE:
    pop bc
    dec b
    jp nz,DRAW_CLOUD
    jp 515Bh

DRAW3:
    push bc
    push de
    ld a,e
    and 1Fh
    cp 22
    jr nc,SPLIT3
    call 4017h
    ld b,3
    outi
    nop
    nop
    nop
    outi
    nop
    nop
    nop
    outi
    nop
    nop
    nop
    jr ROW_END3
SPLIT3:
    ld a,e
    and 1Fh
    ld b,a
    ld a,24
    sub b
    ld b,a
    ld a,3
    sub b
    push af
    call 401Eh
    pop af
    ld b,a
    ld a,e
    and 0E0h
    ld e,a
    call 401Eh
ROW_END3:
    pop de
    call NEXT_ROW
    pop bc
    djnz DRAW3
    ret

DRAW4:
    push bc
    push de
    ld a,e
    and 1Fh
    cp 21
    jr nc,SPLIT4
    call 4017h
    ld b,4
    outi
    nop
    nop
    nop
    outi
    nop
    nop
    nop
    outi
    nop
    nop
    nop
    outi
    nop
    nop
    nop
    jr ROW_END4
SPLIT4:
    ld a,e
    and 1Fh
    ld b,a
    ld a,24
    sub b
    ld b,a
    ld a,4
    sub b
    push af
    call 401Eh
    pop af
    ld b,a
    ld a,e
    and 0E0h
    ld e,a
    call 401Eh
ROW_END4:
    pop de
    call NEXT_ROW
    pop bc
    djnz DRAW4
    ret

DRAW5:
    push bc
    push de
    ld a,e
    and 1Fh
    cp 20
    jr nc,SPLIT5
    call 4017h
    ld b,5
    outi
    nop
    nop
    nop
    outi
    nop
    nop
    nop
    outi
    nop
    nop
    nop
    outi
    nop
    nop
    nop
    outi
    nop
    nop
    nop
    jr ROW_END5
SPLIT5:
    ld a,e
    and 1Fh
    ld b,a
    ld a,24
    sub b
    ld b,a
    ld a,5
    sub b
    push af
    call 401Eh
    pop af
    ld b,a
    ld a,e
    and 0E0h
    ld e,a
    call 401Eh
ROW_END5:
    pop de
    call NEXT_ROW
    pop bc
    djnz DRAW5
    ret

DRAW6:
    push bc
    push de
    ld a,e
    and 1Fh
    cp 19
    jr nc,SPLIT6
    call 4017h
    ld b,6
    outi
    nop
    nop
    nop
    outi
    nop
    nop
    nop
    outi
    nop
    nop
    nop
    outi
    nop
    nop
    nop
    outi
    nop
    nop
    nop
    outi
    nop
    nop
    nop
    jr ROW_END6
SPLIT6:
    ld a,e
    and 1Fh
    ld b,a
    ld a,24
    sub b
    ld b,a
    ld a,6
    sub b
    push af
    call 401Eh
    pop af
    ld b,a
    ld a,e
    and 0E0h
    ld e,a
    call 401Eh
ROW_END6:
    pop de
    call NEXT_ROW
    pop bc
    djnz DRAW6
    ret

; Cloud records are in cyclic vertical order. Rotate the drawing start so
; wrapped clouds and the top rows are updated first. The four-row lookahead
; includes outgoing blank edges at coarse transitions.
FIND_FIRST:
    ld hl,0E212h
    ld b,9
    ld c,24
FIND_CLOUD:
    ld a,(hl)
    and 3
    rlca
    rlca
    rlca
    ld d,a
    inc hl
    ld a,(hl)
    rlca
    rlca
    rlca
    and 7
    or d
    add a,4
    cp 24
    jr c,FIND_KEY
    sub 24
FIND_KEY:
    cp c
    jr nc,FIND_NEXT
    ld c,a
    ld a,l
    dec a
    dec a
    ld (0E80Ch),a
FIND_NEXT:
    inc hl
    inc hl
    djnz FIND_CLOUD
    ret
NEXT_COLUMN:
    inc e
    ld a,e
    and 1Fh
    cp 24
    ret c
    ld a,e
    sub 24
    ld e,a
    ret
NEXT_ROW:
    ld a,e
    add a,32
    ld e,a
    jr nc,NEXT_ROW_CHECK
    inc d
NEXT_ROW_CHECK:
    ld a,d
    cp 7Bh
    ret nz
    ld d,78h
    ret
MOVE_CELLS:
    ld b,9
MOVE_ONE:
    push bc
    push hl
    ld a,(hl)
    inc hl
    ld l,(hl)
    ld h,a
    add hl,de
    ld a,l
    and 1Fh
    cp 18h
    jr nz,MOVE_RIGHT
    ld a,l
    and 0E0h
    jr MOVE_L
MOVE_RIGHT:
    cp 1Fh
    jr nz,MOVE_Y
    ld a,l
    add a,18h
    jr nc,MOVE_L
    inc h
MOVE_L:
    ld l,a
MOVE_Y:
    ld a,h
    cp 77h
    jr nz,MOVE_TOP
    inc h
    inc h
    inc h
MOVE_TOP:
    cp 7Bh
    jr nz,MOVE_SAVE
    dec h
    dec h
    dec h
MOVE_SAVE:
    ld b,h
    ld c,l
    pop hl
    ld (hl),b
    inc hl
    ld (hl),c
    inc hl
    inc hl
    pop bc
    djnz MOVE_ONE
    ret
DIRECTIONS:
'''

SLOT_SOURCE = '''
SLOT:
    di
    call 0138h
    rrca
    rrca
    and 3
    ld c,a
    ld b,0
    ld hl,0FCC1h
    add hl,bc
    ld a,(hl)
    and 80h
    or c
    ld c,a
    inc hl
    inc hl
    inc hl
    inc hl
    ld a,(hl)
    and 0Ch
    or c
    ld h,80h
    call 0024h
    di
    ld a,0C3h
    jp 4206h
'''


def cloud_pixels(rom, width, map_address, vram):
    names = rom[map_address-0x4000:map_address-0x4000+width*4]
    return {(x,y) for y in range(32) for x in range(width*8)
            if vram[0x2000 + names[y//8*width+x//8]*8+y%8] & (128 >> (x%8))}


def make_tables(rom, graficos):
    v = graficos.vram_del_titulo(rom)
    clouds = [(6, 5, cloud_pixels(rom,6,0x6921,v)),
              (4, 3, cloud_pixels(rom,4,0x6981,v))]
    maps = []
    tile = FIRST
    for width, inner_width, pixels in clouds:
        names = bytearray([0x0a] * (width*4))
        for y in range(1,4):
            for x in range(1,width):
                names[y*width+x] = tile
                tile += 1
        maps.append(bytes(names))
    assert tile == FIRST+24
    frames = bytearray()
    checks = 0
    for dy in range(8):
        for dx in range(8):
            frame = bytearray()
            for (_, width, pixels), names in zip(clouds,maps):
                shifted = {(x+dx,y+dy) for x,y in pixels}
                assert all(8 <= x < (width+1)*8 and 8 <= y < 32 for x,y in shifted)
                encoded = bytearray()
                for ty in range(1,4):
                    for tx in range(1,width+1):
                        for sy in range(8):
                            encoded.append(sum(128>>sx for sx in range(8)
                                               if (tx*8+sx,ty*8+sy) in shifted))
                # Decode independently through the name map. Every translated
                # pixel must survive, including boundaries between tiles.
                decoded=set()
                first=min(t for t in names if t != 0x0a)
                for y in range(32):
                    for x in range((width+1)*8):
                        t=names[y//8*(width+1)+x//8]
                        if t != 0x0a and encoded[(t-first)*8+y%8] & (128>>(x%8)):
                            decoded.add((x,y))
                assert decoded == shifted
                frame.extend(encoded)
                checks += 1
            assert len(frame) == FRAME_BYTES
            frames.extend(frame)
    assert len(frames)==0x3000
    # These character colors are uniform in every era; relocating the small
    # cloud into the same range does not change its palette.
    for era in range(1,6):
        vr,_=graficos.vram_de_la_partida(rom,era)
        assert len(set(vr[0x110:0x340])) == 1, ('cloud palette',era)
        assert vr[0x2000:0x2800] == vr[0x2800:0x3000] == vr[0x3000:0x3800], ('shared patterns',era)
    return bytes(frames),maps,checks



def draw_descriptors(base=0x8C00, tile_offset=0):
    headers=bytearray()
    data=bytearray()
    for first,inner_width in ((0x31,3),(0x22,5)):
        for dy in (-1,0,1):
            for dx in (-1,0,1):
                width=inner_width+(dx!=0)
                height=3+(dy!=0)
                ox=0 if dx==1 else 1
                oy=0 if dy==1 else 1
                address=base+18*8+len(data)
                headers.extend(bytes([width,height,ox,oy])+address.to_bytes(2,'little')+bytes(2))
                for y in range(oy,oy+height):
                    for x in range(ox,ox+width):
                        data.append(first+tile_offset+(y-1)*inner_width+x-1
                                    if 1<=y<=3 and 1<=x<=inner_width else 0x0a)
    assert len(headers)==18*8
    assert len(headers)+len(data)<0x800
    return bytes(headers+data)

def load_graphics(disassembly_path):
    helper = disassembly_path / 'tools' / 'graficos.py'
    if not helper.is_file():
        raise SystemExit(
            f'Missing external helper: {helper}\n'
            'See https://github.com/antxiko/TimePilot-disassembly '
            'and pass its local directory with --disassembly.')
    spec = importlib.util.spec_from_file_location('timepilot_external_graphics', helper)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def build(input_path, output_path, disassembly_path):
    if sys.flags.optimize:
        raise SystemExit('Run Python without -O: build assertions must stay enabled.')
    if input_path.resolve() == output_path.resolve():
        raise SystemExit('Input and output paths must be different.')
    if not input_path.is_file():
        raise SystemExit(f'Input ROM not found: {input_path}')
    original=input_path.read_bytes()
    if hashlib.sha256(original).hexdigest()!=EXPECTED:
        raise SystemExit('ROM incompatível: use a revisão do disassembly (SHA-256 '+EXPECTED+'). Nenhuma saída foi gravada.')
    frames,maps,checks=make_tables(original, load_graphics(disassembly_path))
    code,labels=asm.assemble(SOURCE.replace('ld de,POINTERS','ld de,0'),ORG)
    directions=bytes(v & 255 for pair in [(0,-2),(1,-2),(2,-2),(2,-1),(2,0),(2,1),(2,2),(1,2),(0,2),(-1,2),(-2,2),(-2,1),(-2,0),(-2,-1),(-2,-2),(-1,-2)] for v in pair)
    # POINTERS is forward referenced; assemble again at its final address.
    ptr_addr=ORG+len(code)+len(directions)
    source=SOURCE.replace('ld de,POINTERS',f'ld de,0x{ptr_addr:04X}')
    code,labels=asm.assemble(source,ORG)
    pointers=b''.join((TABLE+i*FRAME_BYTES).to_bytes(2,'little') for i in range(64))
    payload=code+directions+pointers
    assert ORG+len(payload)<=0x8C00
    slot,slot_labels=asm.assemble(SLOT_SOURCE,0x7f1e)
    assert 0x7f1e+len(slot)<=0x8000
    rom=bytearray(original)+bytearray([255])*0x4000
    patches=[]
    def patch(address,expected,new):
        offset=address-0x4000
        assert rom[offset:offset+len(expected)]==expected,hex(address)
        assert len(expected)==len(new)
        rom[offset:offset+len(new)]=new
        patches.append({'address':hex(address),'before':expected.hex(),'after':new.hex()})
    def hook(address,expected,label,jump=False):
        target=labels[label]
        patch(address,bytes.fromhex(expected),bytes([0xc3 if jump else 0xcd])+target.to_bytes(2,'little'))
    hook(0x403d,'3a50e0','FINE')
    hook(0x40ca,'2180e3','PREPARE')
    hook(0x42d1,'cd974c','SNAP')
    hook(0x469c,'2100e1','RESET')
    hook(0x5083,'2110e2','ARM',True)
    patch(0x4203,bytes.fromhex('f33ec3'),bytes.fromhex('c31e7f'))
    # SCREEN 2 pattern mask: all screen thirds share the table at 2000h.
    # Colors retain the original configuration. Sprite patterns are separate.
    patch(0x4d09,bytes([7]),bytes([4]))
    patch(0x7f1e,bytes([255])*len(slot),slot)
    for base,m in zip((0x6921,0x6981),maps):
        patch(base,original[base-0x4000:base-0x4000+4*len(m)],m*4)
    rom[ORG-0x4000:ORG-0x4000+len(payload)]=payload
    desc=draw_descriptors()
    rom[0x4C00:0x4C00+len(desc)]=desc
    second=draw_descriptors(0x8E00,24)
    rom[0x4E00:0x4E00+len(second)]=second
    rom[TABLE-0x4000:]=frames
    assert len(rom)==32768
    output_path.parent.mkdir(parents=True,exist_ok=True)
    output_path.write_bytes(rom)
    report={'input':str(input_path),'input_sha256':EXPECTED,
            'output':str(output_path),'output_sha256':hashlib.sha256(rom).hexdigest(),
            'size':len(rom),'code_bytes':len(code),'payload_bytes':len(payload),
            'pixel_checks':checks,'labels':labels,'patches':patches,
            'ram':'E800-E815', 'display_groups':{'A':'34-57','B':'58-81'}, 'strategy':'sixteen headings with half-pixel accumulators; hidden prepare and next-IRQ commit','pattern_frames':'9000-BFFF'}
    output_path.with_suffix('.build.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    output_path.with_suffix('.asm').write_text(source,encoding='utf-8')
    print(json.dumps({k:report[k] for k in ('output','size','code_bytes','pixel_checks','output_sha256')},indent=2))

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--input',type=Path,required=True,help='Original 16 KiB ROM supplied locally by the user')
    p.add_argument('--disassembly',type=Path,required=True,help='External TimePilot-disassembly directory containing tools/graficos.py')
    p.add_argument('--output',type=Path,default=ROOT/'build/timepilot-fino-v7.rom')
    a=p.parse_args()
    build(a.input,a.output,a.disassembly)
