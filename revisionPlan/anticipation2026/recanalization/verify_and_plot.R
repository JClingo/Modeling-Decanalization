# Independent statistics verification and scientific figures; base R only.
args <- commandArgs(trailingOnly=TRUE)
root <- if(length(args)) args[1] else 'revisionPlan/anticipation2026/recanalization'
d <- read.csv(file.path(root,'trial_metrics.csv'),check.names=FALSE)
summ <- read.csv(file.path(root,'phase_summary.csv'),check.names=FALSE)
matched <- read.csv(file.path(root,'baseline_matched_ids.csv'))
conditions <- c('zero','quarter-floor','half-floor','three-quarter-floor','keep','half-exact')
near <- function(a,b) stopifnot(isTRUE(all.equal(a,b,tolerance=2e-8,check.attributes=FALSE)))
values <- function(condition,phase,metric,ids=0:249) {
  x <- d[d$condition==condition & d$phase==phase,]
  stopifnot(nrow(x)==250,!anyDuplicated(x$trial))
  x[match(ids,x$trial),metric]
}
for(i in seq_len(nrow(summ))) {
  r <- summ[i,];x <- values(r$condition,r$phase,r$metric)
  near(r$mean,mean(x));near(r$sd,sd(x));near(r$median,median(x))
  near(r$minimum,min(x));near(r$maximum,max(x))
  margin <- qt(.975,249)*sd(x)/sqrt(250)
  near(r$ci95_low,mean(x)-margin);near(r$ci95_high,mean(x)+margin)
}
verify <- function(name,sensitivity=FALSE) {
  table <- read.csv(file.path(root,name),check.names=FALSE)
  rawp <- numeric(nrow(table))
  for(i in seq_len(nrow(table))) {
    r <- table[i,];ids <- 0:249
    if(r$method=='paired-baseline-matched') {
      ids <- matched$trial[matched$condition==r$condition & matched$reference==r$reference]
    }
    x <- values(r$condition,r$phase,r$metric,ids)
    y <- values(r$reference,r$phase,r$metric,ids)
    if(r$method %in% c('Welch-change','paired-ID-change')) {
      x <- x-values(r$condition,1,r$metric,ids)
      y <- y-values(r$reference,1,r$metric,ids)
    }
    paired <- startsWith(r$method,'paired')
    se2 <- if(paired) var(x-y)/length(x) else var(x)/length(x)+var(y)/length(y)
    if(se2==0) {ci <- rep(mean(x)-mean(y),2);pp <- as.numeric(mean(x)==mean(y))}
    else {test <- t.test(x,y,paired=paired);ci <- test$conf.int;pp <- test$p.value}
    near(r$n_cdr,length(x));near(r$n_ccc,length(y))
    near(r$difference,mean(x)-mean(y));near(r$ci95_low,ci[1]);near(r$ci95_high,ci[2]);near(r$p,pp)
    rawp[i] <- pp
  }
  for(phase in c(2,3)) for(method in unique(table$method)) {
    families <- if(sensitivity) unique(table$comparison_family) else 'all'
    for(family in families) {
      ix <- which(table$phase==phase & table$method==method)
      if(sensitivity) ix <- ix[table$comparison_family[ix]==family]
      near(table$p_holm[ix],p.adjust(rawp[ix],method='holm'))
    }
  }
  nrow(table)
}
np <- verify('primary_contrasts.csv');nc <- verify('versus_current.csv')
na <- verify('all_pairwise.csv');ns <- verify('sensitivity.csv',TRUE)
stopifnot(nrow(d)==5250,nrow(summ)==189,np==24,nc==20,na==60,ns==176)
writeLines(sprintf('PASS: R independently reproduced %d descriptive rows, %d CCC contrasts, %d current-rule contrasts, %d all-pair contrasts and %d sensitivities, including intervals, p values and Holm families.',nrow(summ),np,nc,na,ns),file.path(root,'r_verification.txt'))

labels <- c('0%','25%, floor','50%, floor','75%, floor','100%','50%, exact')
colors <- c('#777777','#ce8b28','#b54f24','#6c7d26','#246c67','#78569c')
metrics <- c('homeostatic-mae','reward-total')
titles <- c('Post-intervention mean absolute h','Post-intervention objective reward')
draw_response <- function() {
  par(mfrow=c(2,1),mar=c(3.4,4,2.6,1),oma=c(.3,0,1,0),mgp=c(2.3,.65,0),tcl=-.2,las=1)
  for(i in 1:2) {
    z <- summ[summ$phase==3 & summ$metric==metrics[i],]
    z <- z[match(c(conditions,'CCC'),z$condition),]
    bounds <- range(c(0,z$ci95_low,z$ci95_high));pad <- diff(bounds)*.05
    plot(NA,xlim=c(.6,6.4),ylim=bounds+c(-pad,pad),xlab='',ylab='',xaxt='n',main=titles[i])
    ccc <- z[7,]
    rect(.6,ccc$ci95_low,6.4,ccc$ci95_high,col=adjustcolor('#1b7089',alpha.f=.12),border=NA)
    abline(h=axTicks(2),col='#e5e5e5');abline(h=ccc$mean,col='#1b7089',lty=2,lwd=1.5)
    axis(1,at=1:6,labels=labels,cex.axis=.82)
    for(j in 1:6) {
      arrows(j,z$ci95_low[j],j,z$ci95_high[j],angle=90,code=3,length=.045,col=colors[j])
      points(j,z$mean[j],pch=if(j==3)15 else 16,col=colors[j],cex=1)
    }
    legend('bottomleft',legend='CCC mean and 95% interval',lty=2,col='#1b7089',bty='n',cex=.8)
    box()
  }
  mtext('HRL counts retained at recanalization; one count per entry in all phases',outer=TRUE,side=3,line=-.2,cex=.8)
}
draw_contrasts <- function() {
  par(mfrow=c(2,1),mar=c(3.4,4,2.6,1),oma=c(.3,0,1,0),mgp=c(2.3,.65,0),tcl=-.2,las=1)
  p <- read.csv(file.path(root,'primary_contrasts.csv'))
  for(i in 1:2) {
    z <- p[p$phase==3 & p$metric==metrics[i],];z <- z[match(conditions,z$condition),]
    bounds <- range(c(0,z$ci95_low,z$ci95_high));pad <- diff(bounds)*.08
    plot(NA,xlim=c(.6,6.4),ylim=bounds+c(-pad,pad),xlab='',ylab='',xaxt='n',
         main=if(i==1)'MAE difference: CDR minus CCC' else 'Reward difference: CDR minus CCC')
    abline(h=axTicks(2),col='#e5e5e5');abline(h=0,lty=2,col='#444444')
    axis(1,at=1:6,labels=labels,cex.axis=.82)
    for(j in 1:6) {
      arrows(j,z$ci95_low[j],j,z$ci95_high[j],angle=90,code=3,length=.045,col=colors[j])
      points(j,z$difference[j],pch=if(j==3)15 else 16,col=colors[j],cex=1)
    }
    box()
  }
  mtext('Welch differences and unadjusted 95% intervals; 250 trials per condition',outer=TRUE,side=3,line=-.2,cex=.8)
}
for(name in c('retention_response','ccc_contrasts')) {
  draw <- if(name=='retention_response') draw_response else draw_contrasts
  pdf(file.path(root,paste0(name,'.pdf')),width=7.6,height=7,pointsize=11);draw();dev.off()
  png(file.path(root,paste0(name,'.png')),width=2280,height=2100,res=300,type='cairo',pointsize=11);draw();dev.off()
}
