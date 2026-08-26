from data.likelihood import DamageLikelihood
from data.regression import DamageRegression
import torch
from data.loader import load_pilot_a_batch
from prior import Prior
from marginal import marginalize

def train(batch, *,seed=0,epochs=2000,lr=0.02):
    
    like=DamageLikelihood()
    reg=DamageRegression()
    pri=Prior()


    reg.initialize_from_batch(batch)
    opt=torch.optim.Adam(list(like.parameters())+list(reg.parameters())+list(pri.parameters()),lr=lr)
    #total param??
    print(f"총 학습될 파라미터 : {sum(p.numel() for p in opt.param_groups[0]["params"])}개")
    

    for epoch in range(epochs):
        out_r=reg(batch)
        # -> 이제 람다들을 만들었으니 이걸... 어떻게 하더라 곱해서 L 하나 내뱉는걸로
        out_l=like(batch,out_r.mu)
        w_batch=pri(batch.pi_ls,batch.pi_lq)
        
        _,log_Py=marginalize(w_batch,out_l.log_L)
        loss=-log_Py.sum()

        opt.zero_grad() #기울기 누적 초기화
        loss.backward()
        opt.step()
        
        if epoch%100==0:
            print(f"{epoch}번째 학습=> loss :{loss}")

    return reg,like,pri



if __name__=="__main__":
    batch=load_pilot_a_batch("raw/재난프로젝트_시정촌별_통계데이터.xlsx",
                             "raw/재난프로젝트_시정촌별_USGS.xlsx")

    train(batch=batch)
