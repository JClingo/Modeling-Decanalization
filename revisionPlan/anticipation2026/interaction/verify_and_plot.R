# Independent base-R verification of factorial contrasts and uncertainty.
args <- commandArgs(trailingOnly=TRUE)
root <- if(length(args)) args[1] else 'revisionPlan/anticipation2026/interaction'
d <- read.csv(file.path(root,'trial_metrics.csv'),check.names=FALSE)
summ <- read.csv(file.path(root,'phase_summary.csv'),check.names=FALSE)
matched <- read.csv(file.path(root,'baseline_matched_ids.csv'))
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
verify <- function(filename,kind) {
  table <- read.csv(file.path(root,filename),check.names=FALSE)
  ps <- numeric(nrow(table))
  for(i in seq_len(nrow(table))) {
    r <- table[i,];ids <- 0:249
    if(kind=='interaction') {
      cells <- c(paste0('k7-',r$first_rule),paste0('k1-',r$first_rule),
                 paste0('k7-',r$second_rule),paste0('k1-',r$second_rule))
      coeff <- c(1,-1,-1,1)
      if(r$method=='paired-baseline-matched') {
        ids <- matched$trial[matched$first_rule==r$first_rule & matched$second_rule==r$second_rule]
      }
    } else if(kind=='simple') {cells <- paste0(c('k7-','k1-'),r$rule);coeff <- c(1,-1)}
    else {cells <- c(r$condition,'CCC');coeff <- c(1,-1)}
    groups <- lapply(cells,function(c) values(c,r$phase,r$metric,ids))
    if(r$method %in% c('Welch-change','paired-ID-change')) {
      groups <- Map(function(x,c) x-values(c,1,r$metric,ids),groups,cells)
    }
    estimate <- sum(coeff*vapply(groups,mean,numeric(1)))
    if(startsWith(r$method,'paired')) {
      collapsed <- (groups[[1]]-groups[[2]])-(groups[[3]]-groups[[4]])
      estimate <- mean(collapsed)
      variance <- var(collapsed)/length(ids);df <- length(ids)-1
      if(variance>0) {
        test <- t.test(collapsed,mu=0)
        ci <- test$conf.int;pp <- test$p.value
        near(df,unname(test$parameter))
      } else {ci <- rep(estimate,2);pp <- as.numeric(estimate==0)}
    } else {
      components <- coeff^2*vapply(groups,var,numeric(1))/length(ids)
      variance <- sum(components)
      df <- if(variance>0) variance^2/sum(components^2/(length(ids)-1)) else 1
      margin <- if(variance>0) qt(.975,df)*sqrt(variance) else 0
      ci <- estimate+c(-margin,margin)
      pp <- if(variance>0) 2*pt(-abs(estimate/sqrt(variance)),df) else as.numeric(estimate==0)
      if(length(groups)==2 && variance>0) {
        test <- t.test(groups[[1]],groups[[2]])
        near(ci,unname(test$conf.int));near(pp,test$p.value)
      }
    }
    near(r$n_per_cell,length(ids));near(r$difference,estimate)
    near(r$se,sqrt(variance));near(r$df,df)
    near(r$ci95_low,ci[1]);near(r$ci95_high,ci[2]);near(r$p,pp)
    ps[i] <- pp
  }
  for(phase in c(2,3)) for(method in unique(table$method)) {
    ix <- which(table$phase==phase & table$method==method)
    stopifnot(length(ix)==if(kind=='ccc')12 else 6)
    near(table$p_holm[ix],p.adjust(ps[ix],method='holm'))
  }
  nrow(table)
}
ni <- verify('interactions.csv','interaction');ns <- verify('simple_rate_effects.csv','simple')
nc <- verify('ccc_contrasts.csv','ccc');nv <- verify('sensitivity.csv','interaction')
stopifnot(nrow(d)==5250,nrow(summ)==189,ni==12,ns==12,nc==24,nv==48)
writeLines(sprintf('PASS: independent R reproduced %d summaries, %d four-cell interactions, %d simple rate effects, %d CCC contrasts and %d interaction sensitivities, including SEs, df, intervals, p values and Holm families.',nrow(summ),ni,ns,nc,nv),file.path(root,'r_verification.txt'))

rules <- c('zero','half','keep');labels <- c('Reset','Halve + floor','Keep all')
metrics <- c('homeostatic-mae','reward-total')
colors <- c('1'='#1b7089','7'='#b54f24')
draw_response <- function() {
  par(mfrow=c(1,2),mar=c(3.6,4,3.2,.8),oma=c(0,0,1.3,0),mgp=c(2.3,.65,0),tcl=-.2,las=1)
  for(i in 1:2) {
    z <- summ[summ$phase==3 & summ$metric==metrics[i],]
    bounds <- range(c(z$ci95_low,z$ci95_high));pad <- diff(bounds)*.1
    plot(NA,xlim=c(.8,3.2),ylim=bounds+c(-pad,pad),xaxt='n',xlab='',ylab='',
         main=if(i==1)'Post-intervention mean absolute h' else 'Post-intervention objective reward',cex.main=.95)
    ccc <- z[z$condition=='CCC',]
    rect(.8,ccc$ci95_low,3.2,ccc$ci95_high,col=adjustcolor('#777777',alpha.f=.1),border=NA)
    abline(h=axTicks(2),col='#e5e5e5');abline(h=ccc$mean,lty=2,col='#777777')
    axis(1,at=1:3,labels=labels,cex.axis=.85)
    for(k in c(1,7)) {
      a <- z[match(paste0('k',k,'-',rules),z$condition),];x <- (1:3)+if(k==1)-.025 else .025
      lines(x,a$mean,col=colors[as.character(k)],lwd=1.4)
      arrows(x,a$ci95_low,x,a$ci95_high,angle=90,code=3,length=.04,col=colors[as.character(k)])
      points(x,a$mean,pch=if(k==1)16 else 17,col=colors[as.character(k)])
    }
    legend('topright',legend=c('1x counting','7x counting','CCC'),col=c(colors,'#777777'),
           lty=c(1,1,2),pch=c(16,17,NA),bty='n',cex=.78)
    box()
  }
  mtext('HRL: counting rate during decanalization x count retention afterward',outer=TRUE,side=3,line=0,cex=.9)
}
draw_interactions <- function() {
  par(mfrow=c(1,2),mar=c(4.3,4,3.2,.8),oma=c(0,0,1.3,0),mgp=c(2.3,.65,0),tcl=-.2,las=1)
  p <- read.csv(file.path(root,'interactions.csv'))
  pairs <- c('zero-half','keep-half','keep-zero')
  for(i in 1:2) {
    z <- p[p$phase==3 & p$metric==metrics[i],]
    z <- z[match(pairs,paste(z$first_rule,z$second_rule,sep='-')),]
    bounds <- range(c(0,z$ci95_low,z$ci95_high));pad <- diff(bounds)*.1
    plot(NA,xlim=c(.7,3.3),ylim=bounds+c(-pad,pad),xaxt='n',xlab='',ylab='',
         main=if(i==1)'Interaction in absolute error' else 'Interaction in received reward',cex.main=.95)
    axis(1,at=1:3,labels=c('Reset vs\nhalf-floor','Keep vs\nhalf-floor','Keep vs\nreset'),cex.axis=.85)
    abline(h=axTicks(2),col='#e5e5e5');abline(h=0,lty=2,col='#444444')
    arrows(1:3,z$ci95_low,1:3,z$ci95_high,angle=90,code=3,length=.045,col='#78569c')
    points(1:3,z$difference,pch=16,col='#78569c')
    box()
  }
  mtext('Difference between 7x-minus-1x effects; four-cell Welch 95% intervals',outer=TRUE,side=3,line=0,cex=.9)
}
for(name in c('factorial_response','interaction_contrasts')) {
  draw <- if(name=='factorial_response') draw_response else draw_interactions
  pdf(file.path(root,paste0(name,'.pdf')),width=10,height=4.4,pointsize=11);draw();dev.off()
  png(file.path(root,paste0(name,'.png')),width=2400,height=1056,res=240,type='cairo',pointsize=11);draw();dev.off()
}
