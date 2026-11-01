# RailSamiksha Dataset Audit & Exploratory Data Analysis

- **Dataset Path:** `C:\Users\Administrator\Desktop\RailSamiksha_Drone_defect_detection_Project\Dataset_pre`
- **Classes Count:** 9

## 1. Split Distribution

| Split   |   Images |   Annotated Images |   Empty Images |   Total BBoxes |   Avg Boxes/Img |
|:--------|---------:|-------------------:|---------------:|---------------:|----------------:|
| train   |      204 |                179 |             25 |            438 |            2.45 |
| valid   |       59 |                 51 |              8 |            141 |            2.76 |
| test    |       33 |                 26 |              7 |             55 |            2.12 |

## 2. Image Resolutions

|   Width |   Height | Color Mode   |   Count |
|--------:|---------:|:-------------|--------:|
|    1536 |     1024 | RGB          |       1 |
|    1672 |      941 | RGB          |       2 |
|    1448 |     1086 | RGB          |       5 |
|    1672 |      940 | RGB          |       2 |
|    1200 |     1200 | RGB          |       1 |
|    2752 |     1536 | RGB          |     196 |
|    1280 |      714 | RGB          |       4 |
|    2880 |     1440 | RGB          |      38 |
|    2816 |     1536 | RGB          |      14 |
|    2516 |     1664 | RGB          |       1 |
|    2730 |     1536 | RGB          |       2 |
|    2338 |     1824 | RGB          |       1 |
|    2390 |     1792 | RGB          |       4 |
|    3552 |     1216 | RGB          |       5 |
|    2750 |     1536 | RGB          |       1 |
|    2444 |     1728 | RGB          |       2 |
|    2818 |     1472 | RGB          |       1 |
|    2392 |     1792 | RGB          |       1 |
|    1984 |     2150 | RGB          |       1 |
|    2300 |     1856 | RGB          |       1 |
|    2016 |     2094 | RGB          |       1 |
|    2394 |     1760 | RGB          |       1 |
|    3275 |     4912 | RGB          |       1 |
|    2586 |     1632 | RGB          |       1 |
|    4160 |      992 | RGB          |       1 |
|    3504 |     1216 | RGB          |       1 |
|     516 |      387 | RGB          |       1 |
|    1376 |      768 | RGB          |       2 |
|    2416 |     1760 | RGB          |       1 |
|    2646 |     1600 | RGB          |       1 |
|     896 |     1200 | RGB          |       1 |
|    3030 |     1376 | RGB          |       1 |

## 3. Class Distribution Across Splits

|   ID | Class Name        |   Train |   Valid |   Test |   Total |   Share (%) |
|-----:|:------------------|--------:|--------:|-------:|--------:|------------:|
|    0 | Ballast Defect    |      25 |       6 |      4 |      35 |        5.52 |
|    1 | Damaged Fastener  |      29 |       6 |      4 |      39 |        6.15 |
|    2 | Foreign Objects   |      77 |      28 |      6 |     111 |       17.51 |
|    3 | Missing Fastener  |      72 |      14 |      8 |      94 |       14.83 |
|    4 | Rail Crack        |      65 |      21 |      3 |      89 |       14.04 |
|    5 | Rail Joint Damage |      22 |       9 |      3 |      34 |        5.36 |
|    6 | Rail Misalignment |       6 |       6 |      2 |      14 |        2.21 |
|    7 | Rail Wear         |      24 |       5 |      2 |      31 |        4.89 |
|    8 | Sleeper Defect    |     118 |      46 |     23 |     187 |       29.5  |

## 4. Object Scale Categories (COCO Criteria)

| Category                                   |   Count |   Percentage (%) |
|:-------------------------------------------|--------:|-----------------:|
| Small (< 32x32 px / < 1024 px²)            |      14 |             2.21 |
| Medium (32x32 to 96x96 px / 1024-9216 px²) |     179 |            28.23 |
| Large (> 96x96 px / > 9216 px²)            |     441 |            69.56 |

## 5. Bounding Box Geometry per Class

| class_name        |   Count |   Mean_W |   Mean_H |   Min_W |   Min_H |   Max_W |   Max_H |   Median_Area |   Mean_AspectRatio |
|:------------------|--------:|---------:|---------:|--------:|--------:|--------:|--------:|--------------:|-------------------:|
| Ballast Defect    |      35 |    635   |    455.3 |      76 |     118 |  1492   |    1132 |      202765   |                1.4 |
| Damaged Fastener  |      39 |    112.6 |    106.4 |      26 |      35 |   231   |     223 |        9215   |                1.2 |
| Foreign Objects   |     111 |    198.9 |    153.9 |      24 |      27 |  1475   |     751 |       12330   |                1.5 |
| Missing Fastener  |      94 |     98.3 |     83.1 |      28 |      29 |   569   |     386 |        5089   |                1.2 |
| Rail Crack        |      89 |    179.2 |    134   |      16 |      25 |   745   |     785 |       12980   |                1.6 |
| Rail Joint Damage |      34 |    546.1 |    354.4 |      55 |      59 |  1951   |     927 |       73081.5 |                2.2 |
| Rail Misalignment |      14 |    302.4 |    436.8 |      63 |     149 |  1200   |    1086 |       73944   |                1.3 |
| Rail Wear         |      31 |    840.3 |    258.5 |      42 |       1 |  2655.3 |     973 |      151257   |               28   |
| Sleeper Defect    |     187 |    409.3 |    477.1 |      33 |      25 |  2752   |    1396 |       67249   |                1.7 |

## 6. Dataset Quality & Integrity Check

- Corrupted images: `0`
- Missing label files: `0`
- Empty label files (background images): `40`
- Invalid bounding boxes: `0`
