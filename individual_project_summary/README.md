# 🛠️ 구현한 기법 : Mixup, Motion Blur, Optimizer 추가 
# 📚 실험한 가설


## 가설
- 데이터 셋을 보니 클래스 간에 유사한 클래스가 많았다. (ex, 뱀의 종류가 구분하기 어려울 정도로 많음)
- 이 클래스를 바로 500개를 구분하는 것보다 대분류(ex, 동물), 중분류(ex, 뱀), 소분류(최종 target 클래스) 구분지어서 loss를 구하는게 더 효과적일 것이라 가정했다.

--- 

## 방법
- swin_base_patch4_window7_224 모델 앞쪽 Stage에서 feature vector를 추출해 대분류 loss를 구하고,
- 중간에서 feature vector를 추출해 중분류 loss를 구하고,
- 기존 loss를 소분류 loss로 생각해 3개의 loss를 가중합해서 backpropagation을 적용했다.

---

## 결과
#### 📚 결과 1 : swin_base_patch4_window7_224 모델의 4번째 Stage의 2번째 block에서 대분류 feature vector를 뽑고, head 전에서 중분류 feature vector를 뽑아서 loss별 가중치 large_loss_weight=0.1, small_loss_weight=0.2, original_loss_weight=0.7로 실험진행
- 실험 의도 1 : 뒤쪽 Stage에서 feature vector를 구해서 loss를 구하면, 모델의 끝부분에서 더 정제된 feature vector를 사용하여 정확도를 높이려는 의도
- 실험 의도 2 : 소분류를 결국 잘 하는게 중요하므로 소분류에 weight를 더 주는 의도

| **Model**            | **Loss별 가중치 적용**              | **Validation Accuracy** | **Public Accuracy** | **Private Accuracy** |
|---------------------|-------------------------------------|-------------------------|---------------------|----------------------|
| **Swin Transformer** | -                              | 0.88192                   | 0.7400         | 0.7460           |
| **Swin Transformer** | Large (0.1), Small (0.2), Original (0.7) | 0.85092                   | ✅**0.8660**          | ✅**0.8640**           |

---

#### 📚 결과 2 : 모델 개선을 위해 large_loss_weight=0.4, small_loss_weight=0.2, original_loss_weight=0.4로 실험진행
- 실험 의도 : 대분류와 소분류에 동일한 가중치를 부여하면, 중분류 성능이 조금 떨어지더라도 대분류와 소분류에서의 학습이 더 강화될 것

| **Model**            | **Loss별 가중치 적용**              | **Validation Accuracy** | **Public Accuracy** | **Private Accuracy** |
|---------------------|-------------------------------------|-------------------------|---------------------|----------------------|
| **Swin Transformer** | Large (0.1), Small (0.2), Original (0.7) | **0.85092**             | ✅**0.8660**          | ✅**0.8640**           |
| **Swin Transformer** | Large (0.4), Small (0.2), Original (0.4) | 0.84526             | -               | -                |

---

#### 📚 결과 3 : Validation Accuracy를 높이기 위해, large_loss_weight=0.5, small_loss_weight=0.3, original_loss_weight=0.2로 실험진행
- 실험 의도 : 대분류 - 중분류 - 소분류 순으로 weight를 주어, 큰 분류에서 분류가 잘 되면 뒤에서도 자연스레 잘 분류되지 않을까 하는 의도

| **Model**            | **Loss별 가중치 적용**              | **Validation Accuracy** | **Public Accuracy** | **Private Accuracy** |
|---------------------|-------------------------------------|-------------------------|---------------------|----------------------|
| **Swin Transformer** | Large (0.1), Small (0.2), Original (0.7) | **0.85092**             | ✅**0.8660**          | ✅**0.8640**           |
| **Swin Transformer** | Large (0.5), Small (0.3), Original (0.2) | 0.84426             | 0.8570          | 0.8580           |

---

#### 📚 결과 4 : 결과3과 같은 조건에 Stratified k fold를 fold=5로 진행
- 실험 의도 : 대분류, 중분류, 소분류 문제에서 클래스 비율이 중요하다고 판단했고, Stratified K-Fold가 매우 유용할 것으로 생각

| **Model**            | **Loss별 가중치 적용**              | **Stratified K-Fold**  | **Validation Accuracy** | **Public Accuracy** | **Private Accuracy** |
|---------------------|-------------------------------------|-----------------------|-------------------------|---------------------|----------------------|
| **Swin Transformer** | Large (0.5), Small (0.3), Original (0.2) | X                 | 0.84426             | 0.8570          | 0.8580           |
| **Swin Transformer** | Large (0.5), Small (0.3), Original (0.2) | O                 | **0.85586**             | ✅**0.9020**          | ✅**0.8970**           |

---

#### 📚 결과 5 : 결과3과 같은 조건에 Stratified k fold를 fold=10로 진행
- 실험 의도 : 데이터 수가 적을 때 fold 수를 세분화하여 모델이 더 다양한 데이터 분포를 학습할 기회를 제공해서 성능을 향상시킬 수 있는 의도

| **Model**            | **Loss별 가중치 적용**              | **Stratified K-Fold**  | **Validation Accuracy** | **Public Accuracy** | **Private Accuracy** |
|---------------------|-------------------------------------|-----------------------|-------------------------|---------------------|----------------------|
| **Swin Transformer** | Large (0.5), Small (0.3), Original (0.2) | X                 | 0.84426             | 0.8570          | 0.8580           |
| **Swin Transformer** | Large (0.5), Small (0.3), Original (0.2) | O (fold=5)        | 0.85586             | 0.9020          | 0.8970           |
| **Swin Transformer** | Large (0.5), Small (0.3), Original (0.2) | O (fold=10)       | ✅**0.86352**             | ✅**0.9040**          | ✅**0.8990**           |

---

#### 📚 결과 6 : swin_base_patch4_window7_224 모델의 3번째 Stage의 18번째 block에서 대분류 feature vector를 뽑고, 4번째 Stage의 2번째 block에서 중분류 feature vector를 뽑아서 loss별 가중치 large_loss_weight=0.5, small_loss_weight=0.3, original_loss_weight=0.2로 실험진행 (Stratified k fold fold=5)
- 실험 의도 : 모델의 앞쪽 Stage는 더 일반적인 특징을 추출하므로, 앞쪽 Stage에서 추출된 덜 세부적인 특징을 사용해 대분류를 분류하면 성능이 오를꺼라는 의도

| **Model**            | **Loss별 가중치 적용**              | **Stratified K-Fold**  | **Feature Vector 뽑아오는 위치** | **Validation Accuracy** | **Public Accuracy** | **Private Accuracy** |
|---------------------|-------------------------------------|-----------------------|---------------------------------|-------------------------|---------------------|----------------------|
| **Swin Transformer** | Large (0.5), Small (0.3), Original (0.2) | O (fold=5)        | **대분류**: 4번째 Stage의 2번째 Block<br>**중분류**: Head 전 | 0.85586             | 0.9020          | 0.8970           |
| **Swin Transformer** | Large (0.5), Small (0.3), Original (0.2) | O (fold=10)      | **대분류**: 4번째 Stage의 2번째 Block<br>**중분류**: Head 전 | 0.86352             | ✅**0.9040**          | ✅**0.8990**           |
| **Swin Transformer** | Large (0.5), Small (0.3), Original (0.2) | O (fold=5)        | **대분류**: 3번째 Stage의 18번째 Block<br>**중분류**: 4번째 Stage의 2번째 Block | 0.84421             | 0.8910          | ✅**0.8890**           |

---

## 회고
- 한계 : 결과 6에서 Stage를 바꾼 부분이 같은 조건의 결과4와 비교했을 때 test_acc가 낮게 나왔는데, 앞쪽 Stage에서 대분류 feature vector를 빼오면 성능이 더 오를 거라는 예상과 달라서 한계에 부딪혔다.
- 아쉬웠던 점 : 시간이 부족해 체계적인 실험을 하지 못 한 점이 아쉽다. 돌이켜 생각해보면, 결과2에서 test 제출을 해보고, 해당 값과 결과3의 값을 비교 후 다음 단계로 실험이 넘어갔어야했는데, 바로 결과3의 결과를 더 발전시켜서 결과2의 결과에 대한 고찰이 부족했다.
- 더하여 여러 cutmix, sweep 등을 시간부족으로 시도해보지 못 한점도 아쉽다.
