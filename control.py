#! /usr/bin/python
# -*- coding:utf-8 -*-

import RPi.GPIO as GPIO
import time

GPIO.setmode(GPIO.BOARD)

current_state=0

#GPIO
IN1 = 16
IN2 = 19
IN3 = 20
IN4 = 26

#left side
ENA = 6
#right side
ENB = 12

GPIO.setup(IN1,GPIO.OUT)
GPIO.setup(IN2,GPIO.OUT)
GPIO.setup(IN3,GPIO.OUT)
GPIO.setup(IN4,GPIO.OUT)

GPIO.setup(ENA,GPIO.OUT)
GPIO.setup(ENB,GPIO.OUT)

pa = GPIO.PWM(ENA, 10)
pb = GPIO.PWM(ENB, 10)

pa.start(100)
pb.start(100)
#change dc
#p.ChangeDutyCycle(dc)

#通过占空比控制转速
def get_speed(vector):
	return min((vector[0]**2+vector[1]**2)**0.5,100)

def init():
	pa.ChangeDutyCycle(100)
	pb.ChangeDutyCycle(100)
	GPIO.output(IN1,GPIO.LOW)
	GPIO.output(IN2,GPIO.LOW)
	GPIO.output(IN3,GPIO.LOW)
	GPIO.output(IN4,GPIO.LOW)


def get_dc(speed):
	return 100-speed

def forward(vector):
	#init()
	speed = get_speed(vector)
	(x,y) = vector
	z = (x**2+y**2)**0.5
	sin0 = y*1.0/z
	cos0 = x*1.0/z
	#通过控制x侧电机占空比控制转向
	speedx = abs(speed*cos0)
	speedy = abs(speed*sin0)


	#y>=0 正转
	if y>=0:
		GPIO.output(IN1,GPIO.HIGH)
		GPIO.output(IN2,GPIO.LOW)
		GPIO.output(IN3,GPIO.HIGH)
		GPIO.output(IN4,GPIO.LOW)
	#y<0 反转
	else:
		GPIO.output(IN1,GPIO.LOW)
		GPIO.output(IN2,GPIO.HIGH)
		GPIO.output(IN3,GPIO.LOW)
		GPIO.output(IN4,GPIO.HIGH)

	if x>=0:
		#使能端A
		pa.ChangeDutyCycle(get_dc(speed))
		#使能端B
		pb.ChangeDutyCycle(get_dc(speed-speedx))
	else:
		#使能端A
		pa.ChangeDutyCycle(get_dc(speed-speedx))
		#使能端B
		pb.ChangeDutyCycle(get_dc(speed))
init()