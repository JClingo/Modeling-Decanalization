# Independent verification and scientific figures; base R only.
args <- commandArgs(trailingOnly=TRUE)
root <- if(length(args)) args[1] else 'revisionPlan/anticipation2026/primary-factor1'
d <- read.csv(file.path(root,'trial_metrics.csv'),check.names=FALSE)
p <- read.csv(file.path(root,'primary_contrasts.csv'),check.names=FALSE)
s <- read.csv(file.path(root,'sensitivity.csv'),check.names=FALSE)
summ <- read.csv(file.path(root,'phase_summary.csv'),check.names=FALSE)
matched <- read.csv(file.path(root,'baseline_matched_ids.csv'))$trial
near <- function(a,b) stopifnot(isTRUE(all.equal(a,b,tolerance=2e-8,check.attributes=FALSE)))
values <- function(order,phase,metric,ids=0:249) {
  x <- d[d$order==order & d$phase==phase,]
  stopifnot(!anyDuplicated(x$trial),nrow(x)==250)
  x[match(ids,x$trial),metric]
}
for(i in seq_len(nrow(summ))) {
  r <- summ[i,]; order <- if(r$condition=='HRL-CDR') 'cdr' else 'ccc'
  x <- values(order,r$phase,r$metric)
  near(r$mean,mean(x));near(r$sd,sd(x));near(r$median,median(x))
  near(r$minimum,min(x));near(r$maximum,max(x))
  margin <- qt(.975,249)*sd(x)/sqrt(250)
  near(r$ci95_low,mean(x)-margin);near(r$ci95_high,mean(x)+margin)
}
verify <- function(table) {
  ps <- numeric(nrow(table))
  for(i in seq_len(nrow(table))) {
    r <- table[i,]; ids <- if(r$method=='paired-baseline-matched') matched else 0:249
    x <- values('cdr',r$phase,r$metric,ids);y <- values('ccc',r$phase,r$metric,ids)
    if(r$method %in% c('Welch-change','paired-ID-change')) {
      x <- x-values('cdr',1,r$metric,ids);y <- y-values('ccc',1,r$metric,ids)
    }
    paired <- startsWith(r$method,'paired')
    se2 <- if(paired) var(x-y)/length(x) else var(x)/length(x)+var(y)/length(y)
    if(se2==0) {ci <- rep(mean(x)-mean(y),2);pp <- as.numeric(mean(x)==mean(y))}
    else {test <- t.test(x,y,paired=paired);ci <- test$conf.int;pp <- test$p.value}
    near(r$n_cdr,length(x));near(r$n_ccc,length(y))
    near(r$difference,mean(x)-mean(y));near(r$ci95_low,ci[1]);near(r$ci95_high,ci[2]);near(r$p,pp)
    ps[i] <- pp
  }
  for(phase in c(2,3)) for(method in unique(table$method)) {
    ix <- which(table$phase==phase & table$method==method)
    stopifnot(length(ix)==9)
    near(table$p_holm[ix],p.adjust(ps[ix],method='holm'))
  }
}
verify(p);verify(s)
stopifnot(length(matched)==249,nrow(d)==1500,nrow(summ)==54,nrow(p)==18,nrow(s)==72)
writeLines('PASS: independent R reproduced 54 descriptive rows, 18 primary contrasts and 72 sensitivity contrasts, with 95% intervals and nine-test Holm families per phase/method.',file.path(root,'r_verification.txt'))
colors <- c(CDR='#b54f24',CCC='#1b7089')
draw <- function(post=FALSE) {
  par(mfrow=c(1,3),mar=c(3.3,3.8,3.5,.8),oma=c(0,0,1,0),mgp=c(2.2,.65,0),tcl=-.22,las=1)
  for(m in c('homeostatic-mae','setpoint-dev','reward-total')) {
    z <- summ[summ$metric==m,];if(post) z <- z[z$phase==3,]
    bounds <- range(c(0,z$ci95_low,z$ci95_high));pad <- diff(bounds)*.05
    plot(NA,xlim=if(post)c(.65,2.35) else c(.8,3.2),ylim=bounds+c(-pad,pad),xlab='',ylab='',xaxt='n')
    title <- c('homeostatic-mae'='Mean absolute h','setpoint-dev'='Population SD of h','reward-total'='Objective reward per phase')[[m]]
    mtext(title,side=3,line=1,cex=.9,font=2)
    abline(h=axTicks(2),col='#e5e5e5')
    if(post) axis(1,at=1:2,labels=c('CDR, factor 1','CCC'))
    else axis(1,at=1:3,labels=c('Pre','During','Post'))
    for(o in c('CDR','CCC')) {
      a <- z[z$condition==paste0('HRL-',o),];a <- a[order(a$phase),]
      x <- if(post) match(o,c('CDR','CCC')) else a$phase+if(o=='CDR')-.035 else .035
      if(!post) lines(x,a$mean,col=colors[o],lwd=1.3)
      keep <- a$ci95_high>a$ci95_low
      if(any(keep)) arrows(x[keep],a$ci95_low[keep],x[keep],a$ci95_high[keep],angle=90,code=3,length=.04,col=colors[o])
      points(x,a$mean,col=colors[o],pch=if(o=='CDR')16 else 17,cex=.9)
    }
    if(!post && m=='homeostatic-mae') legend('topleft',legend=c('CDR, factor 1','CCC'),col=colors,pch=c(16,17),lty=1,bty='n',cex=.8)
    box()
  }
  mtext('HRL: one count per entry in all phases; 250 trials per condition',outer=TRUE,side=3,line=-.2,cex=.85)
}
for(post in c(FALSE,TRUE)) {
  name <- if(post) 'post_outcomes' else 'phase_outcomes'
  pdf(file.path(root,paste0(name,'.pdf')),width=10,height=3.8,pointsize=11);draw(post);dev.off()
  png(file.path(root,paste0(name,'.png')),width=2400,height=912,res=240,type='cairo',pointsize=11);draw(post);dev.off()
}
