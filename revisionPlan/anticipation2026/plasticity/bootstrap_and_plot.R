# Base-R verification, bootstrap relative effects and scientific figures.
args <- commandArgs(trailingOnly=TRUE)
root <- if(length(args)) args[1] else 'revisionPlan/anticipation2026/plasticity'
d <- read.csv(file.path(root,'trial_metrics.csv'),check.names=FALSE)
p <- read.csv(file.path(root,'primary_contrasts.csv'),check.names=FALSE)
s <- read.csv(file.path(root,'sensitivity.csv'),check.names=FALSE)
q <- read.csv(file.path(root,'factor_pairwise.csv'),check.names=FALSE)
summary <- read.csv(file.path(root,'phase_summary.csv'),check.names=FALSE)
relative <- read.csv(file.path(root,'relative_effects.csv'),check.names=FALSE)
matched <- read.csv(file.path(root,'baseline_matched_ids.csv'),check.names=FALSE)
factors <- c(0,1,2,4,7)
outcomes <- c('homeostatic-mae','reward-total')
near <- function(a,b) stopifnot(isTRUE(all.equal(a,b,tolerance=2e-8,check.attributes=FALSE)))
values <- function(condition,phase,metric) {
 x <- d[d$condition==condition & d$phase==phase,];x[order(x$trial),metric]
}
for(i in seq_len(nrow(summary))) {
 r <- summary[i,]; x <- values(r$condition,r$phase,r$metric)
 margin <- qt(.975,length(x)-1)*sd(x)/sqrt(length(x))
 near(r$mean,mean(x));near(r$sd,sd(x));near(r$median,median(x))
 near(r$ci95_low,mean(x)-margin);near(r$ci95_high,mean(x)+margin)
}
verify <- function(table,pairwise=FALSE) {
 ps <- numeric(nrow(table))
 for(i in seq_len(nrow(table))) {
  r <- table[i,]
  condition <- if(pairwise)paste0('CDR-',r$higher_factor) else r$condition
  reference <- if(pairwise)paste0('CDR-',r$lower_factor) else r$reference
  x <- values(condition,r$phase,r$metric);y <- values(reference,r$phase,r$metric)
  if(r$method=='paired-baseline-matched') {
   ids <- matched$trial[matched$condition==condition & matched$reference==reference]+1
   x <- x[ids];y <- y[ids]
  }
  if(r$method %in% c('Welch-change','paired-ID-change')) {
   x <- x-values(condition,1,r$metric);y <- y-values(reference,1,r$metric)
  }
  paired <- startsWith(r$method,'paired')
  se2 <- if(paired)var(x-y)/length(x) else var(x)/length(x)+var(y)/length(y)
  if(se2==0) {ci <- rep(mean(x)-mean(y),2);pp <- as.numeric(mean(x)==mean(y))}
  else {t <- t.test(x,y,paired=paired);ci <- t$conf.int;pp <- t$p.value}
  near(r$difference,mean(x)-mean(y));near(r$ci95_low,ci[1]);near(r$ci95_high,ci[2]);near(r$p,pp)
  ps[i] <- pp
 }
 for(phase in c(2,3)) for(method in unique(table$method)) {
  ids <- which(table$phase==phase & table$method==method)
  near(table$p_holm[ids],p.adjust(ps[ids],method='holm'))
 }
}
verify(p);verify(q,TRUE);verify(s)
writeLines(sprintf('PASS: base R independently reproduced %d descriptive rows, %d primary contrasts, %d secondary factor contrasts and %d sensitivity contrasts, with intervals and Holm corrections.',nrow(summary),nrow(p),nrow(q),nrow(s)),file.path(root,'r_verification.txt'))

set.seed(261026)
B <- 10000
boot <- list()
for(condition in c(paste0('CDR-',factors),'CCC')) {
 x <- cbind(values(condition,3,outcomes[1]),values(condition,3,outcomes[2]))
 indices <- matrix(sample.int(nrow(x),B*nrow(x),replace=TRUE),nrow=B)
 boot[[condition]] <- sapply(1:2,function(j)rowMeans(matrix(x[indices,j],nrow=B)))
 near(boot[[condition]][1,],colMeans(x[indices[1,],,drop=FALSE]))
}
relative$ci95_low <- relative$ci95_high <- NA_real_
for(i in seq_len(nrow(relative))) {
 r <- relative[i,];j <- match(r$metric,outcomes)
 direction <- if(j==1)-1 else 1
 a <- values(r$condition,3,r$metric);b <- values(r$reference,3,r$metric)
 near(r$improvement_percent,direction*100*(mean(a)-mean(b))/mean(b))
 samples <- direction*100*(boot[[r$condition]][,j]-boot[[r$reference]][,j])/boot[[r$reference]][,j]
 ci <- quantile(samples,c(.025,.975),names=FALSE)
 relative$ci95_low[i] <- ci[1];relative$ci95_high[i] <- ci[2]
}
write.csv(relative,file.path(root,'relative_bootstrap.csv'),row.names=FALSE)
writeLines('10,000 independent condition-level trial resamples; base R set.seed(261026); within each condition, the same resampled trial indices are used for MAE and reward. Percentile intervals are descriptive, not multiplicity-adjusted.',file.path(root,'bootstrap_protocol.txt'))

colors <- c('CDR-0'='#555555','CDR-1'='#277f91','CDR-2'='#d46a35','CDR-4'='#76519b','CDR-7'='#4a8522','CCC'='#111111')
titles <- c('homeostatic-mae'='Mean absolute h (lower is better)',
 'reward-total'='HRL reward (higher is better)',
 'setpoint-dev'='Population SD of h','homeostatic-fraction-within-5'='Fraction of samples within +/-5')
metrics <- names(titles)
device_pair <- function(name,draw,width=7.2,height=5.6) {
 pdf(file.path(root,paste0(name,'.pdf')),width=width,height=height,pointsize=11);draw();dev.off()
 png(file.path(root,paste0(name,'.png')),width=width*300,height=height*300,res=300,pointsize=11,type='cairo');draw();dev.off()
}
device_pair('factor_response',function() {
 par(mfrow=c(2,2),cex=1,mar=c(3.8,4.4,3.4,1),mgp=c(2.8,.7,0),tcl=-.25,las=1)
 for(m in metrics) {
  z <- summary[summary$phase==3 & summary$metric==m,]
  a <- z[match(paste0('CDR-',factors),z$condition),];b <- z[z$condition=='CCC',]
  bounds <- range(c(a$ci95_low,a$ci95_high,b$ci95_low,b$ci95_high))
  pad <- diff(bounds)*.1
  plot(NA,xlim=c(-.35,7.35),ylim=bounds+c(-pad,pad),xaxt='n',xlab='Decanalized traversal factor',ylab='',main='')
  mtext(titles[[m]],side=3,line=1,cex=.9,font=2)
  rect(-.35,b$ci95_low,7.35,b$ci95_high,col='#0000000d',border=NA)
  abline(h=axTicks(2),col='#e5e5e5');abline(h=b$mean,lty=2,col='#333333')
  axis(1,at=factors,labels=factors)
  lines(factors,a$mean,col='#888888')
  arrows(factors,a$ci95_low,factors,a$ci95_high,angle=90,code=3,length=.045,col=colors[a$condition])
  points(factors,a$mean,pch=16,col=colors[a$condition],cex=.9)
  if(m==metrics[1])legend('topright',legend='CCC mean and 95% interval',lty=2,col='#333333',bty='n',cex=.75)
  box()
 }
})
device_pair('relative_response',function() {
 par(mfrow=c(1,2),cex=1,mar=c(4,4.5,4,1),mgp=c(2.8,.7,0),tcl=-.25,las=1)
 for(m in outcomes) {
  z <- relative[relative$metric==m & relative$reference=='CDR-1',]
  z$factor <- as.numeric(sub('CDR-','',z$condition));z <- z[order(z$factor),]
  bounds <- range(c(0,z$ci95_low,z$ci95_high));pad <- diff(bounds)*.1
  plot(NA,xlim=c(-.35,7.35),ylim=bounds+c(-pad,pad),xaxt='n',xlab='Decanalized traversal factor',ylab='Improvement over factor 1 (%)',main='')
  mtext(if(m==outcomes[1])'Post-intervention absolute regulation' else 'Post-intervention HRL reward',side=3,line=1,cex=.9,font=2)
  abline(h=axTicks(2),col='#e5e5e5');abline(h=0,lty=2)
  axis(1,at=factors,labels=factors)
  arrows(z$factor,z$ci95_low,z$factor,z$ci95_high,angle=90,code=3,length=.045,col=colors[z$condition])
  points(z$factor,z$improvement_percent,pch=16,col=colors[z$condition]);points(1,0,pch=1,col=colors['CDR-1'])
  box()
 }
},height=3.7)
device_pair('phase_outcomes',function() {
 par(mfrow=c(2,2),cex=1,mar=c(3.5,4.1,3.3,1),mgp=c(2.6,.7,0),tcl=-.25,las=1)
 for(m in metrics) {
  z <- summary[summary$metric==m,];bounds <- range(c(z$ci95_low,z$ci95_high));pad <- diff(bounds)*.08
  plot(NA,xlim=c(.85,3.15),ylim=bounds+c(-pad,pad),xaxt='n',xlab='',ylab='',main='')
  mtext(titles[[m]],side=3,line=1,cex=.9,font=2)
  axis(1,at=1:3,labels=c('Pre','During','Post'));abline(h=axTicks(2),col='#e5e5e5')
  for(condition in c(paste0('CDR-',factors),'CCC')) {
   a <- z[z$condition==condition,];a <- a[order(a$phase),]
   offset <- (match(condition,names(colors))-3.5)*.018;x <- a$phase+offset
   lines(x,a$mean,col=colors[condition],lty=if(condition=='CCC')2 else 1)
   keep <- a$ci95_high>a$ci95_low
   if(any(keep))arrows(x[keep],a$ci95_low[keep],x[keep],a$ci95_high[keep],angle=90,code=3,length=.025,col=colors[condition])
   points(x,a$mean,pch=if(condition=='CCC')17 else 16,cex=.6,col=colors[condition])
  }
  if(m==metrics[1])legend('topleft',legend=names(colors),col=colors,pch=c(rep(16,5),17),lty=c(rep(1,5),2),bty='n',cex=.65,ncol=2)
  box()
 }
})
