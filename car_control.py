#! /usr/bin/python
# -*- coding:utf-8 -*-

import RPi.GPIO as GPIO
import time

GPIO.setwarnings(False)
GPIO.setmode(GPIO.BCM)


#GPIO
IN1 = 19
IN2 = 16
IN3 = 26
IN4 = 20

#left side
ENA = 8
#right side
ENB = 7

GPIO.setup(IN1,GPIO.OUT)
GPIO.setup(IN2,GPIO.OUT)
GPIO.setup(IN3,GPIO.OUT)
GPIO.setup(IN4,GPIO.OUT)

GPIO.setup(ENA,GPIO.OUT)
GPIO.setup(ENB,GPIO.OUT)

pa = GPIO.PWM(ENA, 60)
pb = GPIO.PWM(ENB, 60)

pa.start(0)
pb.start(0)
#change dc
#p.ChangeDutyCycle(dc)

#通过占空比控制转速
def get_speed(vector):
	return min((vector[0]**2+vector[1]**2)**0.5,100)

def init():
	pa.ChangeDutyCycle(0)
	pb.ChangeDutyCycle(0)
	GPIO.output(IN1,GPIO.LOW)
	GPIO.output(IN2,GPIO.LOW)
	GPIO.output(IN3,GPIO.LOW)
	GPIO.output(IN4,GPIO.LOW)

def forward(vector):
	init()
	speed = get_speed(vector)
	(x,y) = vector
	z = (x**2+y**2)**0.5
	if z!=0:
		sin0 = y*1.0/z
		cos0 = x*1.0/z
	else:
		sin0=cos0=0
	#通过控制x侧电机占空比控制转向
	speedx = abs(speed*cos0)
	speedy = abs(speed*sin0)
	print "speed:",speed,speedx,speedy

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

	print "speed:",speed
	if x>=0:
		#使能端A
		#pa.ChangeDutyCycle(100)
		pa.ChangeDutyCycle(speed)
		#使能端B
		#pb.ChangeDutyCycle(100)
		pb.ChangeDutyCycle(speed-speedx)
	else:
		#使能端A
		#pa.ChangeDutyCycle(100)
		pa.ChangeDutyCycle(speed-speedx)
		#使能端B
		#pb.ChangeDutyCycle(100)
		pb.ChangeDutyCycle(speed)
init()
