"""
遗留的数据处理脚本 (从 raw_dataset/csvs/medical_ds/IM_内科/数据处理.py 移动)
用于从 CSV 文件处理医学数据

注: 此脚本已被 generate_dataset.py 取代，仅作为参考保留
"""

asklist = []
answerlist = []

# 原始处理逻辑，已弃用
# with open('内科5000-33000.csv') as f:
#     for i in range(0,5000):
#         lin = f.readline()[0:-1].split(',')
#         if i==0:
#             continue        
#         if len(lin) == 4:
#             if len(lin[1]+','+lin[2])<200 and len(lin[3])<200:
#                 asklist.append(lin[1]+','+lin[2])
#                 answerlist.append(lin[3])
#
# with open('内科.txt','w') as f:
#     for i in range(len(asklist)):
#         f.write(asklist[i]+'\n'+answerlist[i]+'\n\n\n')
